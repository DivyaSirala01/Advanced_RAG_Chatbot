"""LLM-based faithfulness: is the answer grounded in retrieved context?"""

from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

_runnable = None


class FaithfulnessResult(BaseModel):
    score: int = Field(
        ge=1,
        le=10,
        description="1 = contradicted or unsupported by context; 10 = fully supported",
    )
    reasoning: str = Field(description="Brief justification for the score")
    grounded: bool = Field(
        description="True if the answer is adequately supported by the context"
    )


def _get_runnable():
    global _runnable
    if _runnable is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        _runnable = llm.with_structured_output(FaithfulnessResult)
    return _runnable


def evaluate_faithfulness(query: str, context: str, answer: str) -> dict:
    """Return score (1–10), reasoning, and grounded flag."""
    if not context.strip():
        return {
            "score": 1,
            "reasoning": "No context was retrieved; answer cannot be grounded.",
            "grounded": False,
        }

    prompt = f"""You check whether the assistant answer is supported ONLY by the given context (no outside knowledge).

User question:
{query}

Context (only source of truth):
{context}

Assistant answer:
{answer}

Rules:
- If the answer introduces facts not in the context, score low and grounded false.
- If context is insufficient but the answer hedges appropriately, score accordingly.
- grounded should be true only if a reasonable reader could justify the answer from the context alone."""

    result = _get_runnable().invoke(prompt)
    return result.model_dump()
