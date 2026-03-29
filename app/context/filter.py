"""Remove weakly relevant chunks using reranker scores (or an optional LLM pass)."""

from __future__ import annotations

from langchain_core.documents import Document

# Keep in sync with ``app.retrieval.reranker.RERANK_MIN_SCORE`` (1–10 scale).
FILTER_MIN_SCORE = 5


def filter_documents(
    query: str,
    documents: list[Document],
    *,
    min_score: int = FILTER_MIN_SCORE,
    use_llm_when_unscored: bool = False,
) -> list[Document]:
    """
    Keep chunks at or above ``min_score`` on the 1–10 relevance scale.

    Prefer ``metadata["rerank_score"]`` set by ``rerank_documents`` (no extra LLM).
    If a chunk has no score and ``use_llm_when_unscored`` is True, score it once
    with the same LLM judge used in reranking.
    """
    if not documents:
        return []

    kept: list[Document] = []

    for doc in documents:
        raw = doc.metadata.get("rerank_score") if doc.metadata else None
        if raw is None and use_llm_when_unscored:
            from app.retrieval.reranker import score_chunk_relevance

            raw = score_chunk_relevance(query, doc.page_content)

        if raw is None:
            kept.append(doc)
            continue

        score = int(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
        if score is None:
            kept.append(doc)
            continue

        if score >= min_score:
            kept.append(doc)

    if not kept:
        return documents

    return kept
