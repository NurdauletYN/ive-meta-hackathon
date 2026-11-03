"""Preflight check result types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: CheckStatus
    message: str
    file: str | None = None
    line: int | None = None
