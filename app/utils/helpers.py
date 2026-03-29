"""Small utilities for the RAG pipeline (e.g. query normalization for caching)."""

from __future__ import annotations

import re
import unicodedata

_NON_WORD_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)
_SPACES = re.compile(r"\s+")


def normalize_query(query: str) -> str:
    """
    Standardise a user query for stable cache keys and fewer near-duplicates.

    Example: ``"WHAT is RAG??"`` → ``"what is rag"``
    """
    if not query:
        return ""
    s = unicodedata.normalize("NFKC", query.strip()).casefold()
    s = _NON_WORD_PUNCT.sub(" ", s)
    s = _SPACES.sub(" ", s).strip()
    return s


standardise_query = normalize_query
