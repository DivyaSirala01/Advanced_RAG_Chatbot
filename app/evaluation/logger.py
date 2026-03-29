"""Append evaluation records for debugging and analysis (JSON Lines)."""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "evaluation_logs.jsonl"


def log_evaluation(data: dict) -> None:
    """Persist query, context, answer, scores, and UTC timestamp."""
    record = {
        **data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
