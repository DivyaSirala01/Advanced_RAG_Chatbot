"""
STEP 6 context engineering: clean and order retrieved chunks before the LLM.

Flow (see ``STEPS/STEP6.md``):

1. **Deduplicate** — drop exact / near-duplicate chunks (save tokens, reduce noise).
2. **Filter** — drop weakly relevant chunks using ``rerank_score`` when present.
3. **Compress** — keep the most important sentences per chunk (keyword trim by default).
4. **Rank** — put the strongest chunks first so the model weights leading context.

The public entry point is :func:`engineer_context`.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.context.compressor import compress_documents
from app.context.context_ranker import rank_documents_by_importance
from app.context.deduplicator import deduplicate_documents
from app.context.filter import filter_documents


def engineer_context(
    query: str,
    documents: list[Document],
    *,
    dedupe_similarity_threshold: float | None = None,
    filter_min_score: int | None = None,
    filter_use_llm_when_unscored: bool = False,
    compress_max_sentences_per_chunk: int | None = None,
    compress_use_llm: bool = False,
) -> list[Document]:
    """
    Entry point for STEP 6: dedupe → filter → compress → rank.

    Call after ``rerank_documents`` so ``metadata["rerank_score"]`` is available.
    Optional kwargs override defaults on each sub-step (see their modules).
    """
    if not documents:
        return []

    dedupe_kw = (
        {"similarity_threshold": dedupe_similarity_threshold}
        if dedupe_similarity_threshold is not None
        else {}
    )
    docs = deduplicate_documents(documents, **dedupe_kw)

    filter_kw: dict = {"use_llm_when_unscored": filter_use_llm_when_unscored}
    if filter_min_score is not None:
        filter_kw["min_score"] = filter_min_score
    docs = filter_documents(query, docs, **filter_kw)

    compress_kw: dict = {"use_llm": compress_use_llm}
    if compress_max_sentences_per_chunk is not None:
        compress_kw["max_sentences_per_chunk"] = compress_max_sentences_per_chunk
    docs = compress_documents(query, docs, **compress_kw)

    docs = rank_documents_by_importance(query, docs)
    return docs
