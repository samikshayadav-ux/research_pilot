"""
RAG Pipeline: PDF extraction, chunking, embeddings, FAISS vector search.
Falls back to TF-IDF keyword search when sentence-transformers is unavailable.
"""

import os
import re
import json
import hashlib
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ── Optional heavy deps ──────────────────────────────────────────────────────

try:
    import pymupdf as fitz  # PyMuPDF ≥ 1.24 (new API)
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import fitz  # PyMuPDF < 1.24 (legacy name)
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False
        logger.warning("PyMuPDF not available – PDF extraction disabled")

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers / faiss not available – using keyword search")

# ── Constants ────────────────────────────────────────────────────────────────

CHUNK_SIZE   = 400   # words per chunk
CHUNK_OVERLAP = 80   # words overlap
TOP_K        = 5     # chunks returned per query
INDEX_DIR    = Path("data/index")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

# ── Embedding model (lazy-loaded) ────────────────────────────────────────────

_model: Optional[Any] = None

def _get_model():
    global _model
    if _model is None and EMBEDDINGS_AVAILABLE:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ── PDF Extraction ───────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Return structured text with per-page content."""
    if not PYMUPDF_AVAILABLE:
        return {"pages": [], "full_text": "", "metadata": {}}

    doc = fitz.open(pdf_path)
    pages = []
    full_text_parts = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text")
        text = _clean_text(text)
        if text.strip():
            pages.append({"page": page_num, "text": text})
            full_text_parts.append(text)

    # Extract basic metadata from first page
    meta = doc.metadata or {}
    full_text = "\n\n".join(full_text_parts)

    # Try to infer title from first non-empty line if not in metadata
    title = meta.get("title", "")
    if not title and pages:
        first_lines = pages[0]["text"].split("\n")
        title = next((ln.strip() for ln in first_lines if len(ln.strip()) > 10), "Unknown Title")

    return {
        "pages": pages,
        "full_text": full_text,
        "metadata": {
            "title":   title[:200],
            "author":  meta.get("author", "Unknown"),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "page_count": len(doc),
        },
    }


def _clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x20-\x7E\n]', '', text)
    return text.strip()


# ── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(pages: List[Dict], paper_id: str) -> List[Dict]:
    """Split page text into overlapping word-level chunks."""
    chunks = []
    chunk_id = 0

    for page_info in pages:
        words = page_info["text"].split()
        page_num = page_info["page"]

        start = 0
        while start < len(words):
            end   = min(start + CHUNK_SIZE, len(words))
            chunk = " ".join(words[start:end])
            chunks.append({
                "chunk_id":  f"{paper_id}_{chunk_id}",
                "paper_id":  paper_id,
                "page":      page_num,
                "text":      chunk,
                "word_start": start,
            })
            chunk_id += 1
            if end == len(words):
                break
            start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


# ── FAISS Index ──────────────────────────────────────────────────────────────

class PaperIndex:
    """Per-session in-memory FAISS (or keyword) index over all uploaded papers."""

    def __init__(self):
        self.chunks:    List[Dict] = []
        self.index:     Optional[Any] = None   # faiss.IndexFlatIP
        self.embeddings: Optional[np.ndarray] = None

    # ── Ingest ────────────────────────────────────────────────────────────

    def add_paper(self, paper_id: str, pages: List[Dict]) -> List[Dict]:
        new_chunks = chunk_text(pages, paper_id)
        self.chunks.extend(new_chunks)
        self._rebuild_index()
        return new_chunks

    def remove_paper(self, paper_id: str):
        self.chunks = [c for c in self.chunks if c["paper_id"] != paper_id]
        self._rebuild_index()

    # ── Build index ───────────────────────────────────────────────────────

    def _rebuild_index(self):
        if not self.chunks:
            self.index = None
            self.embeddings = None
            return

        if EMBEDDINGS_AVAILABLE:
            model = _get_model()
            texts = [c["text"] for c in self.chunks]
            vecs  = model.encode(texts, show_progress_bar=False, batch_size=32)
            vecs  = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
            self.embeddings = vecs.astype("float32")
            dim = vecs.shape[1]
            self.index = faiss.IndexFlatIP(dim)
            self.index.add(self.embeddings)
        else:
            # Build lightweight TF-IDF for keyword search
            self._build_tfidf()

    def _build_tfidf(self):
        """Simple keyword index using term frequency."""
        from collections import defaultdict, Counter
        self._term_index: Dict[str, List[int]] = defaultdict(list)
        for i, chunk in enumerate(self.chunks):
            for word in set(chunk["text"].lower().split()):
                self._term_index[word].append(i)

    # ── Query ─────────────────────────────────────────────────────────────

    def search(self, query: str, paper_id: Optional[str] = None, top_k: int = TOP_K) -> List[Dict]:
        if not self.chunks:
            return []

        # Filter to specific paper if requested
        if paper_id:
            subset_indices = [i for i, c in enumerate(self.chunks) if c["paper_id"] == paper_id]
            if not subset_indices:
                return []
        else:
            subset_indices = list(range(len(self.chunks)))

        if EMBEDDINGS_AVAILABLE and self.index is not None:
            return self._faiss_search(query, subset_indices, top_k)
        else:
            return self._keyword_search(query, subset_indices, top_k)

    def _faiss_search(self, query: str, subset_indices: List[int], top_k: int) -> List[Dict]:
        model  = _get_model()
        q_vec  = model.encode([query], show_progress_bar=False)
        q_vec  = q_vec / (np.linalg.norm(q_vec, axis=1, keepdims=True) + 1e-9)
        q_vec  = q_vec.astype("float32")

        # Search full index then filter to subset
        k_fetch = min(len(self.chunks), top_k * 10)
        scores, indices = self.index.search(q_vec, k_fetch)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx in subset_indices:
                chunk = dict(self.chunks[idx])
                chunk["score"] = float(score)
                results.append(chunk)
                if len(results) >= top_k:
                    break
        return results

    def _keyword_search(self, query: str, subset_indices: List[int], top_k: int) -> List[Dict]:
        from collections import Counter
        subset_set = set(subset_indices)
        query_words = query.lower().split()
        scores: Dict[int, int] = Counter()

        for word in query_words:
            for idx in getattr(self, '_term_index', {}).get(word, []):
                if idx in subset_set:
                    scores[idx] += 1

        ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
        results = []
        for idx, score in ranked:
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)

        # If nothing matched, return first top_k chunks from subset
        if not results:
            results = [dict(self.chunks[i]) for i in subset_indices[:top_k]]
            for r in results:
                r["score"] = 0.0
        return results

    # ── Snapshot ──────────────────────────────────────────────────────────

    def get_chunks_for_paper(self, paper_id: str) -> List[Dict]:
        return [c for c in self.chunks if c["paper_id"] == paper_id]


# ── Singleton index ──────────────────────────────────────────────────────────

_paper_index = PaperIndex()


def get_index() -> PaperIndex:
    return _paper_index


# ── Helpers for keyword extraction ──────────────────────────────────────────

_STOP_WORDS = set("""
a about above after again against all also am an and any are aren't as at be because been
before being below between both but by can't cannot could couldn't did didn't do does doesn't
doing don't down during each few for from further get got had hadn't has hasn't have haven't
having he he'd he'll he's her here here's hers herself him himself his how how's i i'd i'll
i'm i've if in into is isn't it it's its itself let's me more most mustn't my myself no nor
not of off on once only or other ought our ours ourselves out over own same shan't she she'd
she'll she's should shouldn't so some such than that that's the their theirs them themselves
then there there's these they they'd they'll they're they've this those through to too under
until up very was wasn't we we'd we'll we're we've were weren't what what's when when's where
where's which while who who's whom why why's will with won't would wouldn't you you'd you'll
you're you've your yours yourself yourselves
""".split())


def extract_keywords(text: str, top_n: int = 15) -> List[str]:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w not in _STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in ranked[:top_n]]


def extract_sections(full_text: str) -> Dict[str, str]:
    """Heuristically extract common paper sections."""
    section_patterns = [
        ("abstract",    r'(?i)\babstract\b'),
        ("introduction", r'(?i)\b1\.?\s*introduction\b'),
        ("related_work", r'(?i)\b(related work|literature review|background)\b'),
        ("methodology",  r'(?i)\b(method|methodology|approach|proposed)\b'),
        ("experiments",  r'(?i)\b(experiment|evaluation|results|performance)\b'),
        ("conclusion",   r'(?i)\b(conclusion|future work|summary)\b'),
        ("references",   r'(?i)\breferences\b'),
    ]

    sections: Dict[str, str] = {}
    lines  = full_text.split('\n')
    n      = len(lines)
    starts: List[Tuple[int, str]] = []

    for i, line in enumerate(lines):
        for name, pattern in section_patterns:
            if re.search(pattern, line) and len(line.strip()) < 80:
                starts.append((i, name))
                break

    for j, (start_i, name) in enumerate(starts):
        end_i = starts[j + 1][0] if j + 1 < len(starts) else n
        sections[name] = "\n".join(lines[start_i:end_i])[:3000]

    if not sections:
        sections["full"] = full_text[:3000]

    return sections
