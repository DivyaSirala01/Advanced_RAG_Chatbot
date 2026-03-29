from langchain_core.documents import Document

from app.cache.semantic_cache import get_cached_answer, store_query_answer
from app.context.engineer_context import engineer_context
from app.core.role_router import get_retriever_for_role
from app.query.final_query import prepare_retrieval_queries
from app.retrieval.reranker import RERANK_MIN_SCORE, rerank_documents
from app.generation.generator import generate_answer
from app.utils.helpers import normalize_query


def _merge_unique_docs(doc_lists: list[list[Document]]) -> list[Document]:
    seen: set[str] = set()
    out: list[Document] = []
    for docs in doc_lists:
        for doc in docs:
            key = doc.page_content.strip()
            if key not in seen:
                seen.add(key)
                out.append(doc)
    return out


def run_pipeline(query: str, role: str = "RAG") -> str:
    # Step 7 — normalize for cache keys; keep original query for retrieval + generation.
    cache_key = normalize_query(query)
    if cache_key:
        hit = get_cached_answer(cache_key)
        if hit is not None:
            return hit

    # Role routing — pick retriever (e.g. RAG vs agentic corpus).
    retriever = get_retriever_for_role(role)

    # Query understanding — rewrite / expand / sub-queries for retrieval.
    prepared = prepare_retrieval_queries(query)

    # Hybrid retrieval — run each sub-query through the retriever.
    doc_lists = [retriever.invoke(q) for q in prepared.retrieval_queries]

    # Merge — dedupe chunk lists from multiple retrieval queries.
    docs = _merge_unique_docs(doc_lists)

    # Reranking — LLM relevance scores, sort, trim (STEP 4+).
    docs = rerank_documents(query, docs, min_score=RERANK_MIN_SCORE)

    # Context engineering — dedupe, filter, compress, rank (STEP 6).
    docs = engineer_context(query, docs)

    # Prompt assembly — single context block for the generator.
    context = "\n\n".join(doc.page_content for doc in docs)

    # Generation — LLM answer from context + user query.
    answer = generate_answer(context, query)

    if cache_key:
        store_query_answer(cache_key, answer)

    return answer


