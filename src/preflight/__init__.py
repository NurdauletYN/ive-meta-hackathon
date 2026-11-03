"""Deterministic store-readiness checks with file/line evidence."""

from .runner import run_preflight
from .types import CheckResult, CheckStatus

__all__ = ["CheckResult", "CheckStatus", "run_preflight"]
