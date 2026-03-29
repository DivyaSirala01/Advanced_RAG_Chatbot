"""LLM-based reranking: score each retrieved chunk for query relevance (1–10), then sort and trim."""

from langchain_core.documents import Document
from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

from app.retrieval.fasiss_vector_store import RETRIEVER_K

# Drop chunks below this LLM relevance score before top-k (optional STEP 4 filtering).
RERANK_MIN_SCORE = 5


class ChunkRelevanceScore(BaseModel):
    """Structured LLM output for a single chunk."""

    score: int = Field(
        ge=1,
        le=10,
        description="1 = irrelevant or off-topic; 10 = directly answers or is essential for the query",
    )


_scoring_runnable = None


def _get_scoring_runnable():
    global _scoring_runnable
    if _scoring_runnable is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        _scoring_runnable = llm.with_structured_output(ChunkRelevanceScore)
    return _scoring_runnable


def score_chunk_relevance(query: str, chunk_text: str) -> int:
    """Query + chunk → LLM → relevance score in 1–10."""
    prompt = f"""You judge how useful this text chunk is for answering the user query.

User query:
{query}

Chunk:
{chunk_text}

Return a single relevance score from 1 to 10.
Rules:
- 1–3: unrelated, misleading, or too vague to help
- 4–6: tangentially related or partial background
- 7–8: clearly relevant, useful context
- 9–10: directly answers the query or contains the key facts needed"""
    result = _get_scoring_runnable().invoke(prompt)
    return result.score


def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int | None = None,
    min_score: int | None = None,
) -> list[Document]:
    """
    Score each chunk, sort by descending relevance, optionally drop chunks below
    min_score, then return the best top_k.

    If min_score is set and no chunk passes, falls back to the top_k unfiltered
    scores so the pipeline still has context.
    """
    if not documents:
        return []

    k = top_k if top_k is not None else RETRIEVER_K
    scored: list[tuple[Document, int]] = []
    for doc in documents:
        score = score_chunk_relevance(query, doc.page_content)
        scored.append((doc, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)

    if min_score is not None:
        # Remove chunks with score < threshold (reduces noise).
        passed = [(doc, s) for doc, s in scored if s >= min_score]
        if passed:
            scored = passed
        # else: keep full ranked list so we never return an empty context

    return [doc for doc, _ in scored[:k]]
