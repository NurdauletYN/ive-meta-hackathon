"""A Pilot plus budget + usage JSONL for one run_id."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .budget import Budget
from .protocol import BudgetExceeded, Pilot, Usage
from .usage_log import DEFAULT_USAGE_PATH, append_usage


class PilotSession:
    def __init__(
        self,
        pilot: Pilot,
        *,
        run_id: str,
        usage_path: Path = DEFAULT_USAGE_PATH,
        max_usd: float | None = None,
    ) -> None:
        self.pilot = pilot
        self.run_id = run_id
        self.usage_path = usage_path
        self.budget = Budget(run_id, max_usd, usage_path) if max_usd is not None else None
        self.last_usage: Usage | None = None

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        tag: str,
    ) -> dict[str, Any]:
        if self.budget is not None:
            self.budget.check()
        model = getattr(self.pilot, "model", self.pilot.name)
        try:
            obj, usage = self.pilot.complete_json(system, user, schema, tag)
        except BudgetExceeded:
            raise
        except Exception as exc:
            append_usage(
                self.usage_path,
                run_id=self.run_id,
                pilot=self.pilot.name,
                stage=tag,
                usage=Usage(0, 0, 0, 0.0, None),
                model=str(model),
                ok=False,
                error=str(exc)[:500],
            )
            raise
        self.last_usage = usage
        append_usage(
            self.usage_path,
            run_id=self.run_id,
            pilot=self.pilot.name,
            stage=tag,
            usage=usage,
            model=str(model),
        )
        if self.budget is not None:
            self.budget.check()
        return obj
