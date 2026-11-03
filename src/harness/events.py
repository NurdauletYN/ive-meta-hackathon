"""Append-only run events (jsonl) plus in-process listeners for the studio UI."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from queue import Queue
from typing import Any

Listener = Callable[[dict[str, Any]], None]


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class EventLog:
    def __init__(self, path: Path | None = None, listeners: list[Listener] | None = None) -> None:
        self.path = path
        self.listeners = list(listeners or [])
        self._lock = threading.Lock()
        self.events: list[dict[str, Any]] = []

    def emit(self, type: str, *, run_id: str, **data: Any) -> dict[str, Any]:
        event = {"ts": now_iso(), "type": type, "run_id": run_id, **data}
        with self._lock:
            self.events.append(event)
            if self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
            listeners = list(self.listeners)
        for listener in listeners:
            listener(event)
        return event


class EventHub:
    """Fan-out for SSE clients. Live events only — history replay mixed old jobs into the UI."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subs: list[Queue] = []

    def publish(self, event: dict[str, Any]) -> None:
        with self._lock:
            subs = list(self._subs)
        for queue in subs:
            queue.put(event)

    def subscribe(self) -> Queue:
        queue: Queue = Queue()
        with self._lock:
            self._subs.append(queue)
        return queue

    def unsubscribe(self, queue) -> None:
        with self._lock:
            if queue in self._subs:
                self._subs.remove(queue)
