"""Order context chunks so the most important ones appear first for the LLM."""

from __future__ import annotations

from langchain_core.documents import Document

from app.context.compressor import _WORD, _query_terms


def _rerank_score_value(doc: Document) -> int | None:
    raw = (doc.metadata or {}).get("rerank_score")
    if raw is None or isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    return None


def _keyword_overlap(query: str, text: str) -> int:
    terms = _query_terms(query)
    if not terms:
        return 0
    chunk_words = set(_WORD.findall(text.lower()))
    return len(terms & chunk_words)


def rank_documents_by_importance(query: str, documents: list[Document]) -> list[Document]:
    """
    Sort chunks for prompting: higher ``rerank_score`` first, then stronger query–chunk
    keyword overlap, then stable original order. Puts the best evidence early so the
    model weights leading context more (STEP 6).
    """
    if not documents:
        return []

    def sort_key(item: tuple[int, Document]) -> tuple[int, int, int]:
        idx, doc = item
        rs = _rerank_score_value(doc)
        primary = -rs if rs is not None else 0
        # Unscored chunks: push after scored ones by using a large tie prefix.
        group = 0 if rs is not None else 1
        overlap = -_keyword_overlap(query, doc.page_content)
        return (group, primary, overlap, idx)

    indexed = list(enumerate(documents))
    indexed.sort(key=sort_key)
    return [documents[i] for i, _ in indexed]
