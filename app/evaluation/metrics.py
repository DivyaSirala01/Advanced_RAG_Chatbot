"""Retrieval quality: context precision (and optional recall-style signal)."""

from langchain_core.documents import Document
from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

from app.retrieval.reranker import score_chunk_relevance

_recall_runnable = None


class ContextCoverage(BaseModel):
    """Approximate 'did we get enough context?' without gold documents."""

    score: int = Field(
        ge=1,
        le=10,
        description="1 = context clearly missing key information; 10 = context plausibly sufficient",
    )
    reasoning: str


def _chunk_texts(retrieved_chunks: list[Document] | list[str]) -> list[str]:
    out: list[str] = []
    for c in retrieved_chunks:
        if isinstance(c, Document):
            t = c.page_content.strip()
        else:
            t = str(c).strip()
        if t:
            out.append(t)
    return out


def compute_context_precision(
    retrieved_chunks: list[Document] | list[str],
    query: str,
    *,
    relevance_threshold: int = 5,
) -> float:
    """Fraction of retrieved chunks judged relevant (LLM score >= threshold)."""
    texts = _chunk_texts(retrieved_chunks)
    if not texts:
        return 0.0
    scores = [score_chunk_relevance(query, t) for t in texts]
    relevant = sum(1 for s in scores if s >= relevance_threshold)
    return relevant / len(texts)


def _get_recall_runnable():
    global _recall_runnable
    if _recall_runnable is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        _recall_runnable = llm.with_structured_output(ContextCoverage)
    return _recall_runnable


def compute_context_recall(query: str, context: str) -> dict:
    """Approximate recall: LLM estimates whether retrieved context is sufficient for the query."""
    if not context.strip():
        return {
            "score": 1,
            "reasoning": "Empty context; nothing was retrieved.",
        }

    prompt = f"""Given only the following context (no outside knowledge), estimate how well it covers what is needed to answer the user question.

User question:
{query}

Retrieved context:
{context}

Score 1–10: how sufficient is this context for a complete, accurate answer?"""

    result = _get_recall_runnable().invoke(prompt)
    return result.model_dump()
