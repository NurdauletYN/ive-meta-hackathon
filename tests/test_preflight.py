"""Preflight check tests: golden pass project and one fail fixture per check."""

from __future__ import annotations

from pathlib import Path

import pytest
from preflight.checks import (
    ALL_CHECKS,
    check_account_deletion,
    check_no_placeholders,
    check_privacy_links,
    check_restore_purchases,
    check_subscription_disclosure,
    check_terms_links,
    check_wcag_contrast,
)
from preflight.runner import run_preflight
from preflight.types import CheckStatus

FIX = Path(__file__).resolve().parent / "fixtures" / "preflight"
PASS = FIX / "pass"


def test_pass_project_all_checks_pass() -> None:
    results = run_preflight(PASS)
    assert len(results) == len(ALL_CHECKS)
    assert all(r.status == CheckStatus.PASS for r in results), [r for r in results if r.status != CheckStatus.PASS]


@pytest.mark.parametrize(
    ("fixture", "check_fn", "check_id"),
    [
        ("fail_privacy", check_privacy_links, "privacy_link"),
        ("fail_terms", check_terms_links, "terms_link"),
        ("fail_delete", check_account_deletion, "account_deletion"),
        ("fail_restore", check_restore_purchases, "restore_purchases"),
        ("fail_disclosure", check_subscription_disclosure, "subscription_disclosure"),
        ("fail_placeholder", check_no_placeholders, "no_placeholders"),
        ("fail_contrast", check_wcag_contrast, "wcag_contrast"),
    ],
)
def test_fail_fixture_triggers_exactly_one_check(
    fixture: str, check_fn, check_id: str
) -> None:
    project = FIX / fixture
    target = check_fn(project)
    assert target.status == CheckStatus.FAIL
    assert target.check_id == check_id
    others = [c for c in ALL_CHECKS if c is not check_fn]
    for other in others:
        result = other(project)
        assert result.status == CheckStatus.PASS, (other.__name__, result)
