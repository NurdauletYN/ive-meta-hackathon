"""Abort a run when estimated spend for run_id meets --max-usd."""

from __future__ import annotations

from pathlib import Path

from .protocol import BudgetExceeded
from .usage_log import spent_for_run


class Budget:
    def __init__(self, run_id: str, max_usd: float, usage_path: Path) -> None:
        if max_usd < 0:
            raise ValueError("max_usd must be >= 0")
        self.run_id = run_id
        self.max_usd = max_usd
        self.usage_path = usage_path

    def spent(self) -> float:
        return spent_for_run(self.usage_path, self.run_id)

    def remaining(self) -> float:
        return self.max_usd - self.spent()

    def check(self) -> None:
        spent = self.spent()
        if spent >= self.max_usd:
            raise BudgetExceeded(self.run_id, spent, self.max_usd)
