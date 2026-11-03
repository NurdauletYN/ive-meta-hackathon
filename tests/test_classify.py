"""Infra vs quality classification."""

from __future__ import annotations

from harness.classify import classify_result, is_infra_error
from meta_client.errors import MetaRequestError, MetaRetryExhaustedError


def test_timeout_is_infra() -> None:
    assert is_infra_error(TimeoutError("timeout: The request"))
    assert is_infra_error(MetaRetryExhaustedError(3, "timeout: The request"))
    assert classify_result(ok=False, error="MetaRetryExhaustedError: timeout") == "infra_fail"
    assert classify_result(ok=False, exc=MetaRequestError(429, "rate")) == "infra_fail"
    assert classify_result(ok=False, exc=MetaRequestError(503, "busy")) == "infra_fail"


def test_gate_fail_is_quality() -> None:
    assert classify_result(ok=False, error="preflight failed") == "quality_fail"


def test_ok_is_pass() -> None:
    assert classify_result(ok=True) == "pass"


def test_run_cap_is_infra() -> None:
    assert classify_result(ok=True, wall_s=901, run_timeout_s=900) == "infra_fail"
