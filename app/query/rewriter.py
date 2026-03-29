"""Rewrite terse or ambiguous queries into clear, standalone search questions."""

from pydantic import BaseModel, Field

from app.generation.generator import llm


class RewrittenQuery(BaseModel):
    """LLM output schema for rewriting."""

    rewritten_query: str = Field(
        description="A clear, grammatical question or statement suitable for retrieval.",
    )


_REWRITER = llm.with_structured_output(RewrittenQuery)

_REWRITE_PROMPT = """You improve user queries for semantic and keyword search in a technical RAG system.

Rules:
- Fix grammar and word order; expand implied context (e.g. RAG, embeddings) only when clearly technical.
- Preserve the user's intent; do not add new constraints they did not ask for.
- If the query is already clear, return it polished with minimal change.
- Output one standalone question or imperative search phrase, not a list.

User query:
{query}"""


def rewrite_query(query: str) -> str:
    """Return a retrieval-friendly phrasing of the user query."""
    text = query.strip()
    if not text:
        return text

    out = _REWRITER.invoke(_REWRITE_PROMPT.format(query=text))
    return out.rewritten_query.strip() or text
