"""Hybrid retrieval: dense (FAISS) + sparse (BM25), merged with reciprocal rank fusion."""

from collections import defaultdict
from itertools import chain
from typing import Any

from langchain_core.documents import Document

from app.retrieval.bm25 import (
    get_agentic_bm25_retriever,
    get_rag_bm25_retriever,
)
from app.retrieval.fasiss_vector_store import (
    RETRIEVER_K,
    get_agentic_faiss_retriever,
    get_rag_faiss_retriever,
)

# RRF constant (typical default); higher c smooths rank differences.
RRF_C = 60


def _doc_key(doc: Document) -> str:
    """Stable key for deduplication and scoring."""
    return doc.page_content.strip()


def reciprocal_rank_fuse(
    doc_lists: list[list[Document]],
    *,
    weights: list[float] | None = None,
    c: int = RRF_C,
) -> list[Document]:
    """Weighted reciprocal rank fusion across ordered result lists."""
    if not doc_lists:
        return []
    n = len(doc_lists)
    weights = weights or [1.0 / n] * n
    if len(weights) != n:
        raise ValueError("weights length must match number of retriever lists")

    #Calculates the score for each document
    scores: dict[str, float] = defaultdict(float)
    for docs, w in zip(doc_lists, weights, strict=True):
        for rank, doc in enumerate(docs, start=1):
            scores[_doc_key(doc)] += w / (rank + c)


    #Removes  duplicates from the results
    def first_seen_unique() -> list[Document]:
        seen: set[str] = set()
        out: list[Document] = []
        for doc in chain.from_iterable(doc_lists):
            key = _doc_key(doc)
            if key not in seen:
                seen.add(key)
                out.append(doc)
        return out

    #Sorts the results by the score
    unique_docs = first_seen_unique()
    unique_docs.sort(key=lambda d: scores[_doc_key(d)], reverse=True)
    return unique_docs


class HybridRetriever:
    """Runs dense + sparse retrievers and fuses results (RRF)."""

    def __init__(
        self,
        dense: Any,
        sparse: Any,
        top_k: int = RETRIEVER_K,
        dense_weight: float = 0.5,
        sparse_weight: float = 0.5,
        rrf_c: int = RRF_C,
    ) -> None:
        self._dense = dense
        self._sparse = sparse
        self._top_k = top_k
        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight
        self._rrf_c = rrf_c

    def invoke(self, query: str) -> list[Document]:
        dense_docs = self._dense.invoke(query)
        sparse_docs = self._sparse.invoke(query)
        fused = reciprocal_rank_fuse(
            [dense_docs, sparse_docs],
            weights=[self._dense_weight, self._sparse_weight],
            c=self._rrf_c,
        )
        # After RRF ranking, keep only the top-k chunks for the LLM context window.
        return fused[: self._top_k]


_rag_hybrid: HybridRetriever | None = None
_agentic_hybrid: HybridRetriever | None = None


def get_rag_hybrid_retriever() -> HybridRetriever:
    global _rag_hybrid
    if _rag_hybrid is None:
        _rag_hybrid = HybridRetriever(get_rag_faiss_retriever(), get_rag_bm25_retriever())
    return _rag_hybrid


def get_agentic_hybrid_retriever() -> HybridRetriever:
    global _agentic_hybrid
    if _agentic_hybrid is None:
        _agentic_hybrid = HybridRetriever(
            get_agentic_faiss_retriever(),
            get_agentic_bm25_retriever(),
        )
    return _agentic_hybrid


def get_hybrid_retriever_for_role(role: str) -> HybridRetriever:
    if role.strip() == "Agentic":
        return get_agentic_hybrid_retriever()
    return get_rag_hybrid_retriever()
