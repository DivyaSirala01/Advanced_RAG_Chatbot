from app.retrieval.hybrid_retrieval import get_hybrid_retriever_for_role


def get_retriever_for_role(role: str):
    """Return the domain hybrid retriever (FAISS + BM25) for the given role."""
    return get_hybrid_retriever_for_role(role)
