"""Multi-query expansion for recall on complex retrieval."""

from pydantic import BaseModel, Field

from app.generation.generator import llm


class ExpandedQueries(BaseModel):
    """LLM output schema for multi-query expansion."""

    queries: list[str] = Field(
        description="2–3 diverse paraphrases that retrieve the same intent from different angles.",
        min_length=1,
        max_length=4,
    )


_EXPANDER = llm.with_structured_output(ExpandedQueries)

_EXPAND_PROMPT = """You generate alternative search queries for hybrid (dense + sparse) retrieval.

Rules:
- Produce {n} distinct paraphrases of the same information need.
- Wording should differ (synonyms, angle: how/what/why, related technical terms).
- Stay on-topic; same domain as the original (e.g. RAG, agents, retrieval).
- Do not repeat the original sentence verbatim; each line must add retrieval diversity.
- Return short queries, one idea each.

Original query:
{query}"""


def expand_queries(query: str, *, max_variants: int = 3) -> list[str]:
    """Return up to `max_variants` extra search strings (excludes the original)."""
    text = query.strip()
    if not text:
        return []

    n = max(1, min(max_variants, 4))
    raw = _EXPANDER.invoke(_EXPAND_PROMPT.format(query=text, n=n))

    seen: set[str] = {text.lower()}
    out: list[str] = []
    for q in raw.queries:
        s = q.strip()
        if not s:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= max_variants:
            break
    return out
