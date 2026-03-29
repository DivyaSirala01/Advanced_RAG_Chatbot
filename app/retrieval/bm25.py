"""Sparse (BM25) retrieval per domain, built from the same texts as FAISS ingestion."""

from langchain_community.document_loaders import TextLoader
from langchain_community.retrievers import BM25Retriever
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ingestion.ingest_data import (
    AGENTIC_PATHS,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    RAG_PATHS,
)
from app.retrieval.fasiss_vector_store import RETRIEVER_K

_rag_bm25_retriever: BM25Retriever | None = None
_agentic_bm25_retriever: BM25Retriever | None = None


def _preprocess(text: str) -> list[str]:
    """Lowercase + whitespace tokenization for stable BM25 matching."""
    return text.lower().split()


def _load_chunked_documents(paths: list[str]) -> list:
    raw_docs = []
    for path in paths:
        raw_docs.extend(TextLoader(path).load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_documents(raw_docs)


def _build_bm25_retriever(paths: list[str]) -> BM25Retriever:
    chunks = _load_chunked_documents(paths)
    return BM25Retriever.from_documents(
        chunks,
        k=RETRIEVER_K,
        preprocess_func=_preprocess,
    )


def get_rag_bm25_retriever() -> BM25Retriever:
    """BM25 retriever over RAG-domain chunks (data/data_rag)."""
    global _rag_bm25_retriever
    if _rag_bm25_retriever is None:
        _rag_bm25_retriever = _build_bm25_retriever(RAG_PATHS)
    return _rag_bm25_retriever


def get_agentic_bm25_retriever() -> BM25Retriever:
    """BM25 retriever over Agentic-domain chunks (data/data_agentic)."""
    global _agentic_bm25_retriever
    if _agentic_bm25_retriever is None:
        _agentic_bm25_retriever = _build_bm25_retriever(AGENTIC_PATHS)
    return _agentic_bm25_retriever


def get_bm25_retriever_for_role(role: str) -> BM25Retriever:
    """Return the BM25 retriever for the given domain role."""
    if role.strip() == "Agentic":
        return get_agentic_bm25_retriever()
    return get_rag_bm25_retriever()
