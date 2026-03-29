"""Semantic cache: map queries to answers and reuse when a new query is similar enough."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from langchain_community.embeddings import OpenAIEmbeddings

DEFAULT_SIMILARITY_THRESHOLD = 0.88
DEFAULT_MAX_ENTRIES = 256

_embeddings: OpenAIEmbeddings | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.asarray(a, dtype=np.float64)
    vb = np.asarray(b, dtype=np.float64)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


@dataclass
class _CacheEntry:
    query: str
    embedding: list[float]
    answer: str


class SemanticCache:
    """Stores (query, embedding, answer) and returns answers for semantically similar queries."""

    def __init__(
        self,
        *,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> None:
        self._similarity_threshold = similarity_threshold
        self._max_entries = max(1, max_entries)
        self._entries: list[_CacheEntry] = []
        self._embeddings = _get_embeddings()

    def lookup(self, query: str) -> str | None:
        """Return a cached answer if a stored query matches exactly or is semantically close enough."""
        q = query.strip()
        if not q:
            return None

        for entry in self._entries:
            if entry.query == q:
                return entry.answer

        q_emb = self._embeddings.embed_query(q)
        best_score = -1.0
        best_answer: str | None = None
        for entry in self._entries:
            score = _cosine_similarity(q_emb, entry.embedding)
            if score >= self._similarity_threshold and score > best_score:
                best_score = score
                best_answer = entry.answer
        return best_answer

    def remember(self, query: str, answer: str) -> None:
        """Persist the query and answer (with embedding) for future reuse."""
        q = query.strip()
        a = answer.strip()
        if not q or not a:
            return

        emb = self._embeddings.embed_query(q)
        self._entries.append(_CacheEntry(query=q, embedding=emb, answer=a))
        while len(self._entries) > self._max_entries:
            self._entries.pop(0)


_default_cache = SemanticCache()


def get_cached_answer(query: str) -> str | None:
    return _default_cache.lookup(query)


def store_query_answer(query: str, answer: str) -> None:
    _default_cache.remember(query, answer)
