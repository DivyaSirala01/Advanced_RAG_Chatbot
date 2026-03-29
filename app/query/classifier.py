"""Classify user queries for adaptive retrieval (simple vs complex, definition, etc.)."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.generation.generator import llm


class QueryType(StrEnum):
    SIMPLE = "simple"
    COMPLEX = "complex"
    DEFINITION = "definition"
    COMPARISON = "comparison"
    MULTI_HOP = "multi_hop"


class QueryClassification(BaseModel):
    """LLM output schema for classification."""

    query_type: Literal[
        "simple",
        "complex",
        "definition",
        "comparison",
        "multi_hop",
    ] = Field(
        description="Primary intent/type of the user query for RAG routing.",
    )


_CLASSIFIER = llm.with_structured_output(QueryClassification)

_CLASSIFY_PROMPT = """You label user questions for a retrieval-augmented QA system.

Categories (pick exactly one):
- simple: brief factual lookup, one clear entity or fact.
- complex: broad or multi-part explanation, needs several ideas or depth.
- definition: asks what something is (terminology, concepts).
- comparison: contrasts two or more options (vs, difference, compare, better).
- multi_hop: answer needs chaining steps, prerequisites, or multiple sub-questions.

User query:
{query}

Return only the best-matching category."""


def classify_query(query: str) -> QueryType:
    """Return the query type used for adaptive rewriting/expansion."""
    text = query.strip()
    if not text:
        return QueryType.SIMPLE

    structured = _CLASSIFIER.invoke(_CLASSIFY_PROMPT.format(query=text))
    try:
        return QueryType(structured.query_type)
    except ValueError:
        return QueryType.SIMPLE
