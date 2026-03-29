"""Orchestrate query understanding: rewrite, classify, then adaptive expansion for retrieval."""

from dataclasses import dataclass

from app.query.classifier import QueryType, classify_query
from app.query.expander import expand_queries
from app.query.rewriter import rewrite_query

__all__ = ["PreparedQuery", "QueryType", "prepare_retrieval_queries"]


@dataclass(frozen=True)
class PreparedQuery:
    """Result of the full query-understanding pass."""

    original: str
    rewritten: str
    query_type: QueryType
    retrieval_queries: list[str]


def _should_expand(qtype: QueryType) -> bool:
    return qtype in (QueryType.COMPLEX, QueryType.COMPARISON, QueryType.MULTI_HOP)


def prepare_retrieval_queries(
    query: str,
    *,
    max_expansions: int = 3,
) -> PreparedQuery:
    """
    Run rewrite → classify → optional multi-query expansion.

    Returns all strings to pass to the retriever (deduping is left to the caller
    after merging chunk lists).
    """
    original = query
    rewritten = rewrite_query(query)
    qtype = classify_query(rewritten)

    if _should_expand(qtype):
        extra = expand_queries(rewritten, max_variants=max_expansions)
        retrieval = [rewritten, *extra] if extra else [rewritten]
    else:
        retrieval = [rewritten]

    return PreparedQuery(
        original=original,
        rewritten=rewritten,
        query_type=qtype,
        retrieval_queries=retrieval,
    )
