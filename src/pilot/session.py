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
        events: Any = None,
    ) -> None:
        self.pilot = pilot
        self.run_id = run_id
        self.usage_path = usage_path
        self.budget = Budget(run_id, max_usd, usage_path) if max_usd is not None else None
        self.last_usage: Usage | None = None
        self.events = events

    def emit(self, type: str, **data: Any) -> None:
        if self.events is not None:
            self.events.emit(type, run_id=self.run_id, **data)

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
        self.emit("pilot_call", stage=tag, model=str(model), status="start")
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
            self.emit("pilot_call", stage=tag, model=str(model), status="error", error=str(exc)[:300])
            raise
        self.last_usage = usage
        self.emit(
            "pilot_call",
            stage=tag,
            model=str(model),
            status="ok",
            input_tokens=usage.input_tokens,
            cached_tokens=usage.cached_tokens,
            output_tokens=usage.output_tokens,
            latency_ms=usage.latency_ms,
            est_cost_usd=usage.est_cost_usd,
        )
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
