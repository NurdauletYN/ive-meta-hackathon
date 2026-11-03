"""Pilot protocol: any model that can return schema-constrained JSON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    latency_ms: float
    est_cost_usd: float | None


class BudgetExceeded(RuntimeError):
    """Raised when --max-usd is exceeded for the current run_id."""

    def __init__(self, run_id: str, spent: float, max_usd: float) -> None:
        self.run_id = run_id
        self.spent = spent
        self.max_usd = max_usd
        super().__init__(f"budget exceeded for run {run_id}: ${spent:.4f} >= ${max_usd:.4f}")


class Pilot(Protocol):
    name: str

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        tag: str,
    ) -> tuple[dict[str, Any], Usage]:
        """Return an object matching `schema`. `tag` is the stage name for the usage log."""
        ...
