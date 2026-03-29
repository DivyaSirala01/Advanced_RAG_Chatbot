"""Drop repeated or near-duplicate chunks so context stays lean and non-redundant."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from langchain_core.documents import Document

# Chunks with similarity >= this (0–1) to an already-kept chunk are skipped.
SIMILARITY_THRESHOLD = 0.92


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def deduplicate_documents(
    documents: list[Document],
    *,
    similarity_threshold: float = SIMILARITY_THRESHOLD,
) -> list[Document]:
    """
    Remove exact duplicates (after normalization) and highly similar chunks.

    Order is preserved: the first occurrence wins, which matches reranked
    ordering (keep the stronger chunk, drop later near-copies).
    """
    if not documents:
        return []

    kept: list[Document] = []
    seen_exact: set[str] = set()
    normalized_kept: list[str] = []

    for doc in documents:
        norm = _normalize(doc.page_content)
        if not norm:
            continue
        if norm in seen_exact:
            continue
        if any(
            _text_similarity(norm, prev) >= similarity_threshold
            for prev in normalized_kept
        ):
            continue
        seen_exact.add(norm)
        normalized_kept.append(norm)
        kept.append(doc)

    return kept
