"""
Agentic layer for ResearchPilot AI.

Six logical agents:
  1. PaperAnalysisAgent     – extracts metadata, topics, methods, datasets
  2. ResearchRAGAgent       – retrieves evidence and generates grounded answers
  3. PaperComparisonAgent   – structured side-by-side comparison
  4. ResearchGapAgent       – identifies limitations and unexplored areas
  5. ResearchDirectionAgent – suggests future directions
  6. LiteratureReviewAgent  – generates structured literature review

When IBM watsonx credentials are available, all generation uses IBM Granite.
Otherwise, every agent falls back to deterministic demo-mode output so the
application is fully usable without credentials.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# ── IBM watsonx (optional) ────────────────────────────────────────────────────

_wx_client  = None
_wx_model_id = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")

def _get_wx_client():
    global _wx_client
    if _wx_client is not None:
        return _wx_client

    api_key  = os.getenv("WATSONX_API_KEY", "")
    url      = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    proj_id  = os.getenv("WATSONX_PROJECT_ID", "")

    if not (api_key and proj_id):
        return None

    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        creds = Credentials(url=url, api_key=api_key)
        _wx_client = ModelInference(
            model_id=_wx_model_id,
            credentials=creds,
            project_id=proj_id,
            params={
                "max_new_tokens": 1024,
                "temperature":    0.3,
                "top_p":          0.9,
            },
        )
        logger.info("IBM watsonx client initialised with model %s", _wx_model_id)
    except Exception as exc:
        logger.warning("Could not initialise watsonx client: %s", exc)
        _wx_client = None

    return _wx_client


def _llm_generate(prompt: str, max_tokens: int = 1024) -> str:
    """Generate text via IBM Granite or fall back to demo stub."""
    client = _get_wx_client()
    if client:
        try:
            resp = client.generate_text(prompt=prompt)
            return resp.strip()
        except Exception as exc:
            logger.warning("watsonx generation failed: %s", exc)
    return None   # caller decides what to do on None


def watsonx_available() -> bool:
    return _get_wx_client() is not None


# ── Utilities ─────────────────────────────────────────────────────────────────

def _truncate(text: str, max_words: int = 800) -> str:
    words = text.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Paper Analysis Agent
# ─────────────────────────────────────────────────────────────────────────────

class PaperAnalysisAgent:
    """Extracts structured metadata from a paper's text."""

    PROMPT_TEMPLATE = """You are a research paper analysis assistant. Analyze the following research paper text and extract structured information.

Paper text (excerpt):
{text}

Return a JSON object with these keys:
- title: string (paper title)
- authors: list of strings
- year: string (publication year or "Unknown")
- abstract: string (brief summary, 2-3 sentences)
- topics: list of strings (main research topics, max 6)
- methods: list of strings (ML/AI/statistical methods used, max 6)
- datasets: list of strings (datasets mentioned, max 6)
- metrics: list of strings (evaluation metrics used)
- key_findings: list of strings (3-5 key findings)
- limitations: list of strings (stated limitations)

Respond with valid JSON only."""

    def analyze(self, paper_id: str, full_text: str, metadata: Dict) -> Dict:
        excerpt = _truncate(full_text, 800)
        prompt  = self.PROMPT_TEMPLATE.format(text=excerpt)
        raw     = _llm_generate(prompt)

        if raw:
            try:
                result = json.loads(_extract_json(raw))
                result["paper_id"] = paper_id
                return result
            except Exception:
                pass

        return self._demo_analyze(paper_id, full_text, metadata)

    def _demo_analyze(self, paper_id: str, full_text: str, metadata: Dict) -> Dict:
        from rag import extract_keywords, extract_sections
        keywords = extract_keywords(full_text, 20)
        sections = extract_sections(full_text)

        # Heuristic topic/method/dataset detection
        METHOD_KWORDS  = {"transformer","bert","gpt","lstm","cnn","attention","diffusion",
                          "neural","reinforcement","classification","regression","clustering",
                          "fine-tuning","pretrain","embedding","rag","retrieval","vae","gan"}
        DATASET_KWORDS = {"dataset","corpus","benchmark","imagenet","coco","squad","glue",
                          "mnist","cifar","wikipedia","arxiv","pubmed","laion"}

        topics   = [k for k in keywords if k not in METHOD_KWORDS and k not in DATASET_KWORDS][:6]
        methods  = [k for k in keywords if k in METHOD_KWORDS][:6]
        datasets = [k for k in keywords if k in DATASET_KWORDS][:6]

        # Fall back to generic tags if nothing detected
        if not topics:   topics   = ["machine learning", "deep learning", "AI"]
        if not methods:  methods  = ["neural network", "supervised learning"]
        if not datasets: datasets = ["benchmark dataset"]

        abstract_text = sections.get("abstract", "")
        abstract = " ".join(abstract_text.split()[:60]) + "…" if abstract_text else \
                   " ".join(full_text.split()[:60]) + "…"

        title = metadata.get("title") or "Research Paper"
        author = metadata.get("author") or "Unknown Author"

        return {
            "paper_id":     paper_id,
            "title":        title,
            "authors":      [a.strip() for a in author.split(",") if a.strip()][:5] or ["Unknown"],
            "year":         _infer_year(full_text),
            "abstract":     abstract,
            "topics":       topics,
            "methods":      methods,
            "datasets":     datasets,
            "metrics":      _extract_metrics(full_text),
            "key_findings": _extract_findings(sections),
            "limitations":  _extract_limitations(sections),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Research RAG Agent
# ─────────────────────────────────────────────────────────────────────────────

class ResearchRAGAgent:
    """Retrieves relevant chunks and generates a grounded answer."""

    PROMPT_TEMPLATE = """You are a research assistant. Answer the question using ONLY the provided context from research papers.
For each key claim, cite the paper and page number in brackets like [PaperTitle, p.X].

Context:
{context}

Question: {question}

Instructions:
- Be precise and factual
- Cite sources for every key point
- If the context does not contain enough information, say so clearly
- Distinguish between what papers say vs your interpretation

Answer:"""

    def answer(self, question: str, chunks: List[Dict], papers_meta: Dict[str, Dict]) -> Dict:
        if not chunks:
            return {
                "answer":   "No relevant content found. Please upload papers related to your question.",
                "sources":  [],
                "mode":     "no_data",
            }

        context_parts = []
        sources       = []

        for chunk in chunks:
            pid   = chunk["paper_id"]
            title = papers_meta.get(pid, {}).get("title", pid)
            page  = chunk.get("page", "?")
            context_parts.append(f"[{title}, p.{page}]\n{chunk['text']}")
            sources.append({"paper_id": pid, "title": title, "page": page,
                            "excerpt": chunk["text"][:200]})

        context = "\n\n---\n\n".join(context_parts)
        prompt  = self.PROMPT_TEMPLATE.format(context=_truncate(context, 600), question=question)
        raw     = _llm_generate(prompt)

        if raw:
            return {"answer": raw, "sources": sources, "mode": "watsonx"}

        # Demo: simple extractive answer
        best  = chunks[0]
        title = papers_meta.get(best["paper_id"], {}).get("title", best["paper_id"])
        answer = (
            f"Based on the retrieved context from **{title}** (p.{best.get('page','?')}):\n\n"
            f"{best['text'][:500]}\n\n"
            f"*[Demo mode: connect IBM watsonx for generative answers that synthesise across all {len(chunks)} retrieved passages.]*"
        )
        return {"answer": answer, "sources": sources, "mode": "demo"}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Paper Comparison Agent
# ─────────────────────────────────────────────────────────────────────────────

class PaperComparisonAgent:
    """Generates a structured comparison table for 2–5 papers."""

    DIMENSIONS = ["problem_statement", "methodology", "model_architecture",
                  "datasets", "metrics", "key_results", "limitations", "future_work"]

    PROMPT_TEMPLATE = """You are a research paper comparison expert.
Compare the following papers across these dimensions:
{dimensions}

Papers:
{papers_json}

Return a JSON object where keys are the dimension names and values are dicts mapping paper_id to a short description string.

Respond with valid JSON only."""

    def compare(self, analyses: List[Dict]) -> Dict:
        if len(analyses) < 2:
            return {"error": "Need at least 2 papers to compare."}

        prompt = self.PROMPT_TEMPLATE.format(
            dimensions=", ".join(self.DIMENSIONS),
            papers_json=json.dumps(
                [{k: v for k, v in a.items()
                  if k in ("paper_id","title","abstract","methods","datasets","key_findings","limitations")}
                 for a in analyses],
                indent=2
            )[:2000],
        )
        raw = _llm_generate(prompt)

        if raw:
            try:
                return json.loads(_extract_json(raw))
            except Exception:
                pass

        return self._demo_compare(analyses)

    def _demo_compare(self, analyses: List[Dict]) -> Dict:
        result: Dict[str, Dict] = {dim: {} for dim in self.DIMENSIONS}

        for a in analyses:
            pid = a["paper_id"]
            result["problem_statement"][pid] = a.get("abstract", "N/A")[:200]
            result["methodology"][pid]       = ", ".join(a.get("methods", ["N/A"]))
            result["model_architecture"][pid]= ", ".join(a.get("methods", ["N/A"]))
            result["datasets"][pid]          = ", ".join(a.get("datasets", ["N/A"]))
            result["metrics"][pid]           = ", ".join(a.get("metrics", ["N/A"]))
            result["key_results"][pid]       = "; ".join(a.get("key_findings", ["N/A"])[:2])
            result["limitations"][pid]       = "; ".join(a.get("limitations", ["Not stated"])[:2])
            result["future_work"][pid]       = "Not explicitly stated (demo mode)"

        return result


# ─────────────────────────────────────────────────────────────────────────────
# 4. Research Gap Agent
# ─────────────────────────────────────────────────────────────────────────────

class ResearchGapAgent:
    """Identifies research gaps and underexplored areas."""

    PROMPT_TEMPLATE = """You are a research gap analysis expert.
Analyze the following collection of research papers and identify:
1. Common stated limitations
2. Underexplored research areas
3. Missing comparisons between approaches
4. Dataset gaps (missing evaluations)
5. Evaluation metric gaps
6. Methodological gaps

Papers summary:
{papers_summary}

Return a JSON object with keys:
common_limitations, underexplored_areas, missing_comparisons, dataset_gaps, evaluation_gaps, methodological_gaps, future_directions

Each value should be a list of strings.
Respond with valid JSON only."""

    def find_gaps(self, analyses: List[Dict]) -> Dict:
        summary = json.dumps(
            [{k: v for k, v in a.items()
              if k in ("title","topics","methods","datasets","limitations","key_findings")}
             for a in analyses],
            indent=2
        )[:2000]

        prompt = self.PROMPT_TEMPLATE.format(papers_summary=summary)
        raw    = _llm_generate(prompt)

        if raw:
            try:
                return json.loads(_extract_json(raw))
            except Exception:
                pass

        return self._demo_gaps(analyses)

    def _demo_gaps(self, analyses: List[Dict]) -> Dict:
        all_limitations  = []
        all_datasets     = set()
        all_methods      = set()
        all_topics       = set()

        for a in analyses:
            all_limitations.extend(a.get("limitations", []))
            all_datasets.update(a.get("datasets", []))
            all_methods.update(a.get("methods", []))
            all_topics.update(a.get("topics", []))

        # Deduplicate limitations by hashing first 50 chars
        seen  = set()
        dedup = []
        for lim in all_limitations:
            key = lim[:50]
            if key not in seen:
                seen.add(key)
                dedup.append(lim)

        n_papers = len(analyses)

        return {
            "common_limitations": dedup[:5] or [
                "Limited evaluation on diverse datasets",
                "Lack of ablation studies",
                "High computational cost not addressed",
            ],
            "underexplored_areas": [
                f"Cross-domain generalisation of {m}" for m in list(all_methods)[:3]
            ] or ["Multi-modal approaches", "Low-resource settings", "Real-world deployment"],
            "missing_comparisons": [
                f"Comparison between {list(all_methods)[i]} and {list(all_methods)[i+1]}"
                for i in range(min(2, len(all_methods)-1))
            ] or ["Direct comparison of state-of-the-art baselines not included"],
            "dataset_gaps": [
                f"Evaluation missing on {d}" for d in list(all_datasets)[:3]
            ] or ["No multilingual benchmark evaluation", "Domain-specific datasets lacking"],
            "evaluation_gaps": [
                "Human evaluation not conducted",
                "Robustness to adversarial examples not tested",
                "Efficiency (latency/throughput) not reported",
            ],
            "methodological_gaps": [
                "Interpretability/explainability of models not addressed",
                "Uncertainty quantification absent",
                f"Only {n_papers} paper(s) considered – broader survey recommended",
            ],
            "future_directions": [
                "Combining " + " and ".join(list(all_methods)[:2]) + " for improved performance",
                "Evaluation on real-world production datasets",
                "Lightweight / edge-deployable variants",
                "Fairness and bias analysis across demographic groups",
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# 5. Research Direction Agent
# ─────────────────────────────────────────────────────────────────────────────

class ResearchDirectionAgent:
    """Suggests concrete future research directions."""

    def suggest(self, analyses: List[Dict], gaps: Dict) -> List[Dict]:
        all_topics  = set()
        all_methods = set()
        for a in analyses:
            all_topics.update(a.get("topics", []))
            all_methods.update(a.get("methods", []))

        future = gaps.get("future_directions", [])
        ue     = gaps.get("underexplored_areas", [])
        dg     = gaps.get("dataset_gaps", [])

        directions = []
        for i, fd in enumerate(future[:4]):
            directions.append({
                "id":          i + 1,
                "title":       fd,
                "description": f"Addressing: {ue[i] if i < len(ue) else 'identified gap'}.",
                "impact":      ["High", "Medium", "High", "Medium"][i % 4],
                "difficulty":  ["Medium", "Hard", "Medium", "Easy"][i % 4],
                "related_gap": dg[i] if i < len(dg) else "general gap",
            })

        if not directions:
            directions = [
                {"id":1,"title":"Scalable evaluation frameworks","description":"Build benchmarks that cover more domains.","impact":"High","difficulty":"Medium","related_gap":"evaluation_gaps"},
                {"id":2,"title":"Efficient model architectures","description":"Reduce compute while maintaining accuracy.","impact":"High","difficulty":"Hard","related_gap":"methodological_gaps"},
            ]

        return directions


# ─────────────────────────────────────────────────────────────────────────────
# 6. Literature Review Agent
# ─────────────────────────────────────────────────────────────────────────────

class LiteratureReviewAgent:
    """Generates a structured literature review."""

    PROMPT_TEMPLATE = """You are an academic writing assistant. Write a structured literature review for the following set of research papers.

Papers:
{papers_json}

The review must have these sections:
1. Introduction (overview of the field and motivation)
2. Existing Approaches (describe each paper's contribution)
3. Comparison of Approaches (similarities and differences)
4. Key Findings (synthesis of results)
5. Limitations (common weaknesses)
6. Research Gaps (what is missing)
7. Future Directions (promising areas)

Write in formal academic style. Cite papers by their title in brackets.
Aim for ~600 words total."""

    def generate(self, analyses: List[Dict], gaps: Dict) -> Dict:
        papers_json = json.dumps(
            [{k: v for k, v in a.items()
              if k in ("title","abstract","topics","methods","datasets","key_findings","limitations")}
             for a in analyses],
            indent=2
        )[:2500]

        prompt = self.PROMPT_TEMPLATE.format(papers_json=papers_json)
        raw    = _llm_generate(prompt)

        if raw:
            return {"text": raw, "mode": "watsonx", "sections": _parse_review_sections(raw)}

        return self._demo_review(analyses, gaps)

    def _demo_review(self, analyses: List[Dict], gaps: Dict) -> Dict:
        titles   = [a.get("title","Unknown") for a in analyses]
        topics   = list({t for a in analyses for t in a.get("topics",[])})[:5]
        methods  = list({m for a in analyses for m in a.get("methods",[])})[:5]
        datasets = list({d for a in analyses for d in a.get("datasets",[])})[:4]
        lims     = gaps.get("common_limitations", ["Limited generalisation"])
        gaps_lst = gaps.get("underexplored_areas", ["Multi-modal settings"])
        future   = gaps.get("future_directions", ["Scalable benchmarks"])

        paper_list = "; ".join(f"[{t}]" for t in titles)
        intro = (
            f"This literature review examines {len(analyses)} research paper(s) in the area of "
            f"{', '.join(topics[:3]) or 'machine learning'}. "
            f"The reviewed works—{paper_list}—collectively advance understanding of "
            f"{', '.join(methods[:3]) or 'neural network'} approaches. "
            f"This review synthesises their contributions, compares methodologies, "
            f"and identifies open challenges."
        )

        approaches = "\n\n".join(
            f"**[{a.get('title','Paper')}]** employs {', '.join(a.get('methods',['deep learning']))} "
            f"on {', '.join(a.get('datasets',['benchmark data']))}. "
            f"{' '.join(a.get('key_findings',['Achieves competitive performance.'])[:2])}"
            for a in analyses
        )

        comparison = (
            f"The reviewed papers share a focus on {', '.join(topics[:2]) or 'AI/ML'} but differ "
            f"in their choice of methodology. "
            f"{'[' + titles[0] + ']'} and {'[' + titles[1] + ']' if len(titles)>1 else 'subsequent works'} "
            f"both leverage {methods[0] if methods else 'supervised learning'}, yet diverge in dataset choices "
            f"({', '.join(datasets[:2]) or 'custom datasets'}) and evaluation protocols."
        )

        findings = (
            f"Across the reviewed works, {methods[0] if methods else 'transformer-based'} approaches "
            f"consistently outperform simpler baselines. Key results include: "
            + "; ".join(
                f.get("key_findings",["N/A"])[0] if f.get("key_findings") else "competitive results"
                for f in analyses[:3]
            ) + "."
        )

        limitations_text  = " ".join(f"({i+1}) {l}" for i, l in enumerate(lims[:3]))
        gaps_text         = " ".join(f"({i+1}) {g}" for i, g in enumerate(gaps_lst[:3]))
        future_text       = " ".join(f"({i+1}) {fd}" for i, fd in enumerate(future[:3]))

        full_text = (
            f"## 1. Introduction\n{intro}\n\n"
            f"## 2. Existing Approaches\n{approaches}\n\n"
            f"## 3. Comparison of Approaches\n{comparison}\n\n"
            f"## 4. Key Findings\n{findings}\n\n"
            f"## 5. Limitations\nCommon limitations include: {limitations_text}\n\n"
            f"## 6. Research Gaps\nNotable gaps include: {gaps_text}\n\n"
            f"## 7. Future Directions\nPromising avenues: {future_text}\n\n"
            f"*[Demo mode — connect IBM watsonx for AI-generated academic prose.]*"
        )

        return {
            "text": full_text,
            "mode": "demo",
            "sections": {
                "introduction":  intro,
                "approaches":    approaches,
                "comparison":    comparison,
                "findings":      findings,
                "limitations":   limitations_text,
                "gaps":          gaps_text,
                "future":        future_text,
            },
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_json(text: str) -> str:
    """Extract first JSON block from a string."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    return match.group(0) if match else text


def _infer_year(text: str) -> str:
    years = re.findall(r'\b(19[89]\d|20[012]\d)\b', text)
    if years:
        from collections import Counter
        return Counter(years).most_common(1)[0][0]
    return "Unknown"


def _extract_metrics(text: str) -> List[str]:
    METRICS = {"accuracy","f1","precision","recall","bleu","rouge","perplexity",
               "auc","map","ndcg","mrr","em","exact match","score","cer","wer"}
    found = []
    lower = text.lower()
    for m in METRICS:
        if m in lower:
            found.append(m.upper() if len(m) <= 4 else m.title())
    return found[:6] or ["Accuracy"]


def _extract_findings(sections: Dict[str, str]) -> List[str]:
    text = sections.get("experiments", sections.get("conclusion", sections.get("full", "")))
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result_sentences = [
        s.strip() for s in sentences
        if any(kw in s.lower() for kw in ["achiev","outperform","result","state-of-the-art","improve","show","demonstrate","surpass"])
        and 15 < len(s) < 200
    ]
    return result_sentences[:4] or ["Achieves competitive performance on standard benchmarks."]


def _extract_limitations(sections: Dict[str, str]) -> List[str]:
    text = sections.get("conclusion", sections.get("full", ""))
    sentences = re.split(r'(?<=[.!?])\s+', text)
    lim_sentences = [
        s.strip() for s in sentences
        if any(kw in s.lower() for kw in ["limit","future","drawback","challenge","not","lack","cannot","fail"])
        and 15 < len(s) < 200
    ]
    return lim_sentences[:3] or ["Limitations not explicitly stated."]


def _parse_review_sections(text: str) -> Dict[str, str]:
    sections = {}
    patterns = {
        "introduction":  r'(?i)1\.?\s*introduction(.*?)(?=\n#+\s*\d|\Z)',
        "approaches":    r'(?i)2\.?\s*existing approaches(.*?)(?=\n#+\s*\d|\Z)',
        "comparison":    r'(?i)3\.?\s*comparison(.*?)(?=\n#+\s*\d|\Z)',
        "findings":      r'(?i)4\.?\s*(?:key\s+)?findings(.*?)(?=\n#+\s*\d|\Z)',
        "limitations":   r'(?i)5\.?\s*limitations(.*?)(?=\n#+\s*\d|\Z)',
        "gaps":          r'(?i)6\.?\s*(?:research\s+)?gaps(.*?)(?=\n#+\s*\d|\Z)',
        "future":        r'(?i)7\.?\s*future(.*?)(?=\n#+\s*\d|\Z)',
    }
    for key, pat in patterns.items():
        m = re.search(pat, text, re.DOTALL)
        sections[key] = m.group(1).strip() if m else ""
    return sections
