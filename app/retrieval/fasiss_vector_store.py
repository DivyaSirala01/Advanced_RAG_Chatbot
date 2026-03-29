from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

RAG_INDEX_DIR = "db/faiss_index_rag"
AGENTIC_INDEX_DIR = "db/faiss_index_agentic"
RETRIEVER_K = 3

_embeddings: OpenAIEmbeddings | None = None
_rag_retriever = None
_agentic_retriever = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings()
    return _embeddings


def get_rag_faiss_retriever():
    """Retriever over the RAG-domain FAISS index."""
    global _rag_retriever
    if _rag_retriever is None:
        db = FAISS.load_local(
            RAG_INDEX_DIR,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        _rag_retriever = db.as_retriever(search_kwargs={"k": RETRIEVER_K})
    return _rag_retriever


def get_agentic_faiss_retriever():
    """Retriever over the Agentic-domain FAISS index."""
    global _agentic_retriever
    if _agentic_retriever is None:
        db = FAISS.load_local(
            AGENTIC_INDEX_DIR,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        _agentic_retriever = db.as_retriever(search_kwargs={"k": RETRIEVER_K})
    return _agentic_retriever
