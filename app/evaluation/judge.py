"""LLM-as-a-judge: relevance, correctness, completeness, and answer helpfulness."""

from langchain_openai.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

_runnable = None


class JudgeResult(BaseModel):
    relevance: int = Field(
        ge=1,
        le=10,
        description=(
            "How directly the answer addresses the user's question and intent. "
            "Low if it only refuses or says the topic is missing—refusal alone is not 'high relevance'."
        ),
    )
    correctness: int = Field(
        ge=1,
        le=10,
        description=(
            "Whether the answer is valid given the context: no false claims, and not misleading. "
            "A safe 'not in context' reply can be mostly correct but should NOT score 10—use ~6–8 when "
            "it is honest but does not deliver the requested substance."
        ),
    )
    completeness: int = Field(
        ge=1,
        le=10,
        description=(
            "Coverage of what the question actually asks for. "
            "If the assistant only declines or says information is absent, score LOW (1–3)—that is not a complete answer."
        ),
    )
    helpfulness: int = Field(
        ge=1,
        le=10,
        description=(
            "Did the answer actually answer the question? "
            "1–3: did not answer (e.g. only refusal or hedge). "
            "4–6: partial. "
            "7–10: fully answered. "
            "'Not in context' / cannot answer is NOT helpful for the user's information need—score 1–3."
        ),
    )
    feedback: str = Field(description="Short qualitative summary")


def _get_runnable():
    global _runnable
    if _runnable is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        _runnable = llm.with_structured_output(JudgeResult)
    return _runnable


def _looks_like_context_refusal(answer: str) -> bool:
    """Heuristic: model declined because context was missing or insufficient."""
    a = answer.lower()
    markers = (
        "cannot answer",
        "can't answer",
        "could not answer",
        "couldn't answer",
        "not in context",
        "not in the context",
        "not contained in the context",
        "not found in the context",
        "unable to answer",
        "no information in the",
        "cannot be answered from",
        "insufficient context",
        "don't have enough context",
        "do not have enough context",
        "not available in the provided",
    )
    return any(m in a for m in markers)


def _apply_refusal_penalties(payload: dict, answer: str) -> dict:
    """Grounded refusals must not look like perfect answers on usefulness axes."""
    if not _looks_like_context_refusal(answer):
        return payload
    r, c, comp, h = (
        payload["relevance"],
        payload["correctness"],
        payload["completeness"],
        payload["helpfulness"],
    )
    payload["relevance"] = min(r, 5)
    payload["correctness"] = min(c, 8)
    payload["completeness"] = min(comp, 3)
    payload["helpfulness"] = min(h, 3)
    return payload


def evaluate_answer(query: str, context: str, answer: str) -> dict:
    """Evaluate usefulness of the answer (1–10 per dimension); faithfulness is evaluated separately."""
    prompt = f"""You evaluate how well the assistant's reply serves the USER'S QUESTION.

Faithfulness (whether the reply sticks to the context only) is scored elsewhere—your job is whether the reply
actually satisfies the user's intent and is useful.

User question:
{query}

Context (source of truth for what was available to the assistant):
{context}

Assistant answer:
{answer}

Scoring rules (all 1–10):
- relevance: Did the answer target what the user asked? If the user wanted a definition or explanation and the assistant only says the information is not in the context, relevance is LOW (about 3–5), not high.
- correctness: Are statements consistent with the context and not misleading? A honest "I cannot answer from this context" can be mostly correct but should score around 6–8, not 10, because it does not verify or deliver requested facts about the topic.
- completeness: Did the answer cover what the question implies? Refusals and "not in context" alone mean LOW completeness (about 1–3).
- helpfulness: Did the reply actually answer the question? Same bands as the field description: 1–3 no real answer; 4–6 partial; 7–10 full answer. "Not in context" / cannot answer → helpfulness 1–3.

If the context is empty or irrelevant but the assistant correctly refuses to invent facts, that is good behavior for grounding—but still score relevance, completeness, and helpfulness LOW because the user did not get an answer.

Add a short feedback string summarizing these axes."""

    result = _get_runnable().invoke(prompt)
    payload = result.model_dump()
    return _apply_refusal_penalties(payload, answer)
