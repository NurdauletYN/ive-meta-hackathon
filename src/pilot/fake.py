"""Offline pilot: returns canned JSON keyed by stage tag. No network."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .protocol import Usage


class FakePilot:
    name = "fake"

    def __init__(
        self,
        scripts: dict[str, list[Any]] | None = None,
        *,
        cost_per_call: float = 0.01,
        cached_tokens: int = 0,
        model: str = "fake",
    ) -> None:
        self._queues: dict[str, list[Any]] = defaultdict(list)
        if scripts:
            for tag, items in scripts.items():
                self._queues[tag] = list(items)
        self.cost_per_call = cost_per_call
        self.cached_tokens = cached_tokens
        self.model = model
        self.calls: list[tuple[str, str]] = []

    def enqueue(self, tag: str, *objs: Any) -> None:
        self._queues[tag].extend(objs)

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        tag: str,
    ) -> tuple[dict[str, Any], Usage]:
        self.calls.append((tag, system, user))
        queue = self._queues.get(tag)
        if not queue:
            raise LookupError(f"FakePilot has no canned response for tag {tag!r}")
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        if not isinstance(item, dict):
            raise TypeError(f"FakePilot canned item for {tag!r} must be a dict")
        usage = Usage(
            input_tokens=len(system) + len(user),
            cached_tokens=self.cached_tokens,
            output_tokens=len(str(item)),
            latency_ms=1.0,
            est_cost_usd=self.cost_per_call,
        )
        return item, usage
