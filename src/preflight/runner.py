"""Run all preflight checks against a Flutter project directory."""

from __future__ import annotations

from pathlib import Path

from .checks import ALL_CHECKS
from .types import CheckResult


def run_preflight(project_dir: Path) -> list[CheckResult]:
    project = project_dir.resolve()
    return [check(project) for check in ALL_CHECKS]
