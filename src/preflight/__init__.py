"""Deterministic store-readiness checks with file/line evidence."""

from .checks import contrast_ratio
from .runner import run_preflight
from .types import CheckResult, CheckStatus

__all__ = ["CheckResult", "CheckStatus", "contrast_ratio", "run_preflight"]
