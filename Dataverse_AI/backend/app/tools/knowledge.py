"""retrieve_knowledge: TF-IDF search over the project knowledge base (methodology,
definitions, rules -- never raw trip rows). No vector DB needed for 7 short files."""
import re
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import KNOWLEDGE_DIR


def _split_paragraphs(text: str, source: str) -> list[dict]:
    """Chunk by markdown section so headers stay attached to their content."""
    sections = re.split(r"(?m)^(#{1,3} .+)$", text)
    chunks = []
    preamble = sections[0].strip()
    if preamble:
        chunks.append(preamble)
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        body = sections[i + 1].strip() if i + 1 < len(sections) else ""
        chunks.append(f"{header}\n{body}".strip())
    return [{"source": source, "text": c} for c in chunks if c]


@lru_cache(maxsize=1)
def _corpus():
    chunks = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        chunks.extend(_split_paragraphs(path.read_text(encoding="utf-8"), path.name))
    return chunks


@lru_cache(maxsize=1)
def _index():
    chunks = _corpus()
    texts = [c["text"] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


def retrieve_knowledge(query: str, top_k: int = 3) -> dict:
    chunks = _corpus()
    vectorizer, matrix = _index()
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix).flatten()
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)

    results = [
        {"source": chunk["source"], "text": chunk["text"], "relevance_score": round(float(score), 4)}
        for score, chunk in ranked[:top_k] if score > 0
    ]
    if not results:
        return {"results": [], "note": "No knowledge-base content matched this query closely enough."}
    return {"results": results}
