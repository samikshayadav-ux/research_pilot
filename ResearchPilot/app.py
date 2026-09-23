"""
ResearchPilot AI — Flask backend
"""

import os
import uuid
import json
import logging
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── App setup ────────────────────────────────────────────────────────────────

BASE_DIR    = Path(__file__).parent
UPLOAD_DIR  = BASE_DIR / "static" / "uploads"
DATA_DIR    = BASE_DIR / "data"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s – %(message)s")
logger = logging.getLogger(__name__)

app  = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024   # 50 MB

# ── In-memory state ───────────────────────────────────────────────────────────
# papers:  { paper_id: { paper_id, filename, title, authors, ... analysis } }

_papers:     dict = {}
_demo_loaded: bool = False

# ── Lazy imports (heavy deps) ─────────────────────────────────────────────────

def _rag():
    import rag
    return rag

def _agents():
    import agents
    return agents

def _demo():
    import demo_data
    return demo_data

# ── Demo mode bootstrap ───────────────────────────────────────────────────────

def _ensure_demo():
    """Load demo papers into state on first call."""
    global _demo_loaded
    if _demo_loaded:
        return
    dd = _demo()
    for paper in dd.DEMO_PAPERS:
        _papers[paper["paper_id"]] = dict(paper)
    _demo_loaded = True


# ── Static / index ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)


# ── System status ──────────────────────────────────────────────────────────────

@app.route("/api/status")
def status():
    _ensure_demo()
    ag = _agents()
    return jsonify({
        "watsonx_available": ag.watsonx_available(),
        "embeddings_available": _rag().EMBEDDINGS_AVAILABLE,
        "pymupdf_available":    _rag().PYMUPDF_AVAILABLE,
        "papers_count":         len(_papers),
        "demo_mode":            not ag.watsonx_available(),
    })


# ── Paper Library ──────────────────────────────────────────────────────────────

@app.route("/api/papers", methods=["GET"])
def list_papers():
    _ensure_demo()
    papers = list(_papers.values())
    # Don't send full chunks back
    safe = [{k: v for k, v in p.items() if k != "_chunks"} for p in papers]
    return jsonify(safe)


@app.route("/api/papers/<paper_id>", methods=["GET"])
def get_paper(paper_id):
    _ensure_demo()
    paper = _papers.get(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404
    safe = {k: v for k, v in paper.items() if k != "_chunks"}
    return jsonify(safe)


@app.route("/api/papers/upload", methods=["POST"])
def upload_paper():
    _ensure_demo()
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    paper_id = str(uuid.uuid4())[:8]
    filename = f"{paper_id}_{file.filename}"
    filepath = UPLOAD_DIR / filename
    file.save(str(filepath))

    rag  = _rag()
    ag   = _agents()

    try:
        # Extract text
        extracted = rag.extract_text_from_pdf(str(filepath))
        pages      = extracted["pages"]
        full_text  = extracted["full_text"]
        meta       = extracted["metadata"]

        if not pages:
            return jsonify({"error": "Could not extract text from PDF. Ensure it is not scanned-only."}), 422

        # Index chunks
        idx = rag.get_index()
        idx.add_paper(paper_id, pages)

        # Analyse
        analysis = ag.PaperAnalysisAgent().analyze(paper_id, full_text, meta)

        paper_record = {
            "paper_id":   paper_id,
            "filename":   file.filename,
            "title":      analysis.get("title") or meta.get("title") or file.filename,
            "authors":    analysis.get("authors", ["Unknown"]),
            "year":       analysis.get("year", "Unknown"),
            "page_count": meta.get("page_count", len(pages)),
            "abstract":   analysis.get("abstract", ""),
            "topics":     analysis.get("topics", []),
            "methods":    analysis.get("methods", []),
            "datasets":   analysis.get("datasets", []),
            "metrics":    analysis.get("metrics", []),
            "key_findings": analysis.get("key_findings", []),
            "limitations": analysis.get("limitations", []),
            "demo":       False,
        }
        _papers[paper_id] = paper_record
        logger.info("Uploaded and indexed paper %s: %s", paper_id, paper_record["title"])
        return jsonify(paper_record), 201

    except Exception as exc:
        logger.exception("Error processing PDF %s", file.filename)
        filepath.unlink(missing_ok=True)
        return jsonify({"error": str(exc)}), 500


@app.route("/api/papers/<paper_id>", methods=["DELETE"])
def delete_paper(paper_id):
    paper = _papers.pop(paper_id, None)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    if not paper.get("demo"):
        filepath = UPLOAD_DIR / f"{paper_id}_{paper['filename']}"
        try:
            filepath.unlink(missing_ok=True)
        except Exception:
            pass
        _rag().get_index().remove_paper(paper_id)

    return jsonify({"success": True})


# ── Dashboard stats ────────────────────────────────────────────────────────────

@app.route("/api/dashboard")
def dashboard():
    _ensure_demo()
    papers = list(_papers.values())

    all_topics   = [t for p in papers for t in p.get("topics",   [])]
    all_methods  = [m for p in papers for m in p.get("methods",  [])]
    all_datasets = [d for p in papers for d in p.get("datasets", [])]
    all_gaps     = []

    # Count frequencies
    from collections import Counter
    topic_counts   = Counter(all_topics).most_common(8)
    method_counts  = Counter(all_methods).most_common(8)
    dataset_counts = Counter(all_datasets).most_common(8)

    # Estimate gap count from limitations
    for p in papers:
        all_gaps.extend(p.get("limitations", []))

    return jsonify({
        "papers_count":   len(papers),
        "topics_count":   len(set(all_topics)),
        "methods_count":  len(set(all_methods)),
        "datasets_count": len(set(all_datasets)),
        "gaps_count":     len(set(all_gaps)),
        "topic_distribution":   [{"name": k, "value": v} for k, v in topic_counts],
        "method_distribution":  [{"name": k, "value": v} for k, v in method_counts],
        "dataset_distribution": [{"name": k, "value": v} for k, v in dataset_counts],
        "papers":         [{
            "title":   p.get("title",""),
            "year":    p.get("year",""),
            "topics":  p.get("topics",[])[:3],
            "methods": p.get("methods",[])[:3],
            "demo":    p.get("demo", False),
        } for p in papers],
    })


# ── Research Chat (RAG) ───────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    _ensure_demo()
    data      = request.get_json(force=True)
    question  = (data.get("question") or "").strip()
    paper_id  = data.get("paper_id")   # optional: restrict to one paper

    if not question:
        return jsonify({"error": "Question is required"}), 400

    rag = _rag()
    ag  = _agents()

    # If using demo papers, return canned demo answers
    real_papers = {pid: p for pid, p in _papers.items() if not p.get("demo")}

    if not real_papers and not paper_id:
        # All papers are demo papers — use demo chunks
        dd     = _demo()
        chunks = []
        for demo_chunks in dd.DEMO_CHUNKS.values():
            chunks.extend(demo_chunks[:2])
        chunks = _keyword_filter_demo_chunks(question, chunks)[:5]
        papers_meta = {p["paper_id"]: p for p in _demo().DEMO_PAPERS}
    else:
        target_pid = paper_id if paper_id and not _papers.get(paper_id, {}).get("demo") else None
        chunks = rag.get_index().search(question, paper_id=target_pid, top_k=5)
        if not chunks and paper_id and _papers.get(paper_id, {}).get("demo"):
            dd     = _demo()
            chunks = dd.DEMO_CHUNKS.get(paper_id, [])[:5]
        papers_meta = _papers

    result = ag.ResearchRAGAgent().answer(question, chunks, papers_meta)
    return jsonify(result)


def _keyword_filter_demo_chunks(query: str, chunks: list) -> list:
    qwords = set(query.lower().split())
    scored = []
    for c in chunks:
        score = sum(1 for w in qwords if w in c["text"].lower())
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored]


# ── Paper question (single-paper chat) ────────────────────────────────────────

@app.route("/api/papers/<paper_id>/ask", methods=["POST"])
def ask_paper(paper_id):
    _ensure_demo()
    paper = _papers.get(paper_id)
    if not paper:
        return jsonify({"error": "Paper not found"}), 404

    data     = request.get_json(force=True)
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required"}), 400

    rag = _rag()
    ag  = _agents()

    if paper.get("demo"):
        dd     = _demo()
        chunks = _keyword_filter_demo_chunks(question, dd.DEMO_CHUNKS.get(paper_id, []))[:3]
    else:
        chunks = rag.get_index().search(question, paper_id=paper_id, top_k=3)

    result = ag.ResearchRAGAgent().answer(question, chunks, {paper_id: paper})
    return jsonify(result)


# ── Paper Comparison ──────────────────────────────────────────────────────────

@app.route("/api/compare", methods=["POST"])
def compare_papers():
    _ensure_demo()
    data = request.get_json(force=True)
    ids  = data.get("paper_ids", [])

    if len(ids) < 2:
        return jsonify({"error": "Select at least 2 papers to compare"}), 400
    if len(ids) > 5:
        return jsonify({"error": "Select at most 5 papers"}), 400

    missing = [pid for pid in ids if pid not in _papers]
    if missing:
        return jsonify({"error": f"Papers not found: {missing}"}), 404

    analyses = [_papers[pid] for pid in ids]
    ag       = _agents()

    # If all papers are demo papers, return canned comparison
    if all(a.get("demo") for a in analyses):
        dd = _demo()
        canned = {k: {pid: v for pid, v in row.items() if pid in ids}
                  for k, row in dd.DEMO_COMPARISON.items()}
        return jsonify({
            "comparison": canned,
            "papers": [{"paper_id": a["paper_id"], "title": a["title"]} for a in analyses],
            "mode": "demo",
        })

    comparison = ag.PaperComparisonAgent().compare(analyses)
    return jsonify({
        "comparison": comparison,
        "papers": [{"paper_id": a["paper_id"], "title": a["title"]} for a in analyses],
        "mode": "watsonx" if ag.watsonx_available() else "demo",
    })


# ── Research Gaps ──────────────────────────────────────────────────────────────

@app.route("/api/gaps", methods=["GET", "POST"])
def research_gaps():
    _ensure_demo()
    analyses = list(_papers.values())
    ag       = _agents()

    if all(a.get("demo") for a in analyses):
        dd = _demo()
        dirs = ag.ResearchDirectionAgent().suggest(dd.DEMO_PAPERS, dd.DEMO_GAPS)
        return jsonify({
            "gaps":       dd.DEMO_GAPS,
            "directions": dirs,
            "mode":       "demo",
        })

    gaps = ag.ResearchGapAgent().find_gaps(analyses)
    dirs = ag.ResearchDirectionAgent().suggest(analyses, gaps)
    return jsonify({
        "gaps":       gaps,
        "directions": dirs,
        "mode": "watsonx" if ag.watsonx_available() else "demo",
    })


# ── Research Landscape (graph) ────────────────────────────────────────────────

@app.route("/api/landscape")
def landscape():
    _ensure_demo()
    papers = list(_papers.values())

    nodes = []
    links = []
    node_ids = set()

    def add_node(nid, label, group, size=10):
        if nid not in node_ids:
            nodes.append({"id": nid, "label": label, "group": group, "size": size})
            node_ids.add(nid)

    for paper in papers:
        pid = paper["paper_id"]
        add_node(pid, paper.get("title","Paper")[:40], "paper", 18)

        for topic in paper.get("topics", [])[:4]:
            tid = f"topic_{topic}"
            add_node(tid, topic, "topic", 12)
            links.append({"source": pid, "target": tid, "type": "has_topic"})

        for method in paper.get("methods", [])[:4]:
            mid = f"method_{method}"
            add_node(mid, method, "method", 12)
            links.append({"source": pid, "target": mid, "type": "uses_method"})

        for dataset in paper.get("datasets", [])[:3]:
            did = f"dataset_{dataset}"
            add_node(did, dataset, "dataset", 10)
            links.append({"source": pid, "target": did, "type": "uses_dataset"})

    return jsonify({"nodes": nodes, "links": links})


# ── Literature Review ──────────────────────────────────────────────────────────

@app.route("/api/review", methods=["POST"])
def literature_review():
    _ensure_demo()
    data = request.get_json(force=True)
    ids  = data.get("paper_ids") or list(_papers.keys())

    analyses = [_papers[pid] for pid in ids if pid in _papers]
    if not analyses:
        return jsonify({"error": "No papers available"}), 400

    ag = _agents()

    if all(a.get("demo") for a in analyses):
        dd = _demo()
        return jsonify({
            "review": dd.DEMO_REVIEW,
            "sections": {},
            "mode": "demo",
        })

    gaps   = ag.ResearchGapAgent().find_gaps(analyses)
    result = ag.LiteratureReviewAgent().generate(analyses, gaps)
    return jsonify({
        "review":   result["text"],
        "sections": result.get("sections", {}),
        "mode":     result.get("mode", "demo"),
    })


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port  = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting ResearchPilot AI on http://127.0.0.1:%d", port)
    app.run(host="127.0.0.1", port=port, debug=debug)
