"""One JSON line per API call (tokens, latency, cost). Used for the eval cost tables."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class CallStats:
    ts: str
    op: str
    model: str
    path: str
    ok: bool
    attempts: int
    latency_ms: float
    status: int | None = None
    input_tokens: int | None = None
    cached_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    images: int | None = None
    est_cost_usd: float | None = None
    error: str | None = None

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="milliseconds")


class UsageLog:
    """Appends CallStats as JSONL and keeps them in memory for the current process."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.records: list[CallStats] = []
        self._lock = threading.Lock()

    def write(self, stats: CallStats) -> None:
        with self._lock:
            self.records.append(stats)
            if self.path is None:
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(stats), ensure_ascii=False) + "\n")
