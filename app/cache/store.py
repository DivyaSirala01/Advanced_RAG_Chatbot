"""MongoDB-backed persistent store for query → answer cache entries (with embeddings)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.environ.get("MONGODB_DB", "advanced_rag")
MONGODB_CACHE_COLLECTION = os.environ.get("MONGODB_CACHE_COLLECTION", "semantic_query_cache")

_client: MongoClient | None = None
_indexes_ensured = False


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


def get_cache_collection() -> Collection[Any]:
    return _get_client()[MONGODB_DB][MONGODB_CACHE_COLLECTION]


def ensure_cache_indexes() -> None:
    """Create indexes once: unique query key, recency for hydration."""
    global _indexes_ensured
    if _indexes_ensured:
        return
    coll = get_cache_collection()
    coll.create_index([("query", ASCENDING)], unique=True, name="uq_query")
    coll.create_index([("updated_at", ASCENDING)], name="idx_updated_at")
    _indexes_ensured = True


@dataclass(frozen=True)
class CacheRecord:
    query: str
    answer: str
    embedding: list[float]


def upsert_cache_record(query: str, answer: str, embedding: list[float]) -> None:
    """Persist or update one cache row keyed by exact ``query`` string."""
    q = query.strip()
    if not q or not answer.strip() or not embedding:
        return

    ensure_cache_indexes()
    coll = get_cache_collection()
    now = datetime.now(timezone.utc)
    coll.update_one(
        {"query": q},
        {
            "$set": {
                "query": q,
                "answer": answer.strip(),
                "embedding": embedding,
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


def get_cache_record_by_query(query: str) -> CacheRecord | None:
    """Load a single row by exact query match."""
    q = query.strip()
    if not q:
        return None

    ensure_cache_indexes()
    doc = get_cache_collection().find_one({"query": q})
    if doc is None:
        return None
    emb = doc.get("embedding")
    if not isinstance(emb, list) or not emb:
        return None
    return CacheRecord(
        query=doc["query"],
        answer=doc["answer"],
        embedding=[float(x) for x in emb],
    )


def fetch_recent_cache_records(limit: int = 10_000) -> list[CacheRecord]:
    """
    Return cache rows newest-first (for rehydrating an in-memory semantic cache).
    ``limit`` caps how many documents are read from MongoDB.
    """
    if limit < 1:
        return []

    ensure_cache_indexes()
    coll = get_cache_collection()
    cursor = (
        coll.find({"embedding": {"$exists": True, "$ne": []}})
        .sort("updated_at", DESCENDING)
        .limit(limit)
    )
    rows: list[CacheRecord] = []
    for doc in cursor:
        emb = doc.get("embedding")
        if not isinstance(emb, list) or not emb:
            continue
        rows.append(
            CacheRecord(
                query=doc["query"],
                answer=doc["answer"],
                embedding=[float(x) for x in emb],
            )
        )
    return rows


def close_mongo_client() -> None:
    """Release the Mongo client (e.g. tests or process shutdown)."""
    global _client, _indexes_ensured
    if _client is not None:
        _client.close()
        _client = None
    _indexes_ensured = False
