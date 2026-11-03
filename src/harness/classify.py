"""Classify a sweep run as pass, quality_fail, or infra_fail. Never mix the last two."""

from __future__ import annotations

import re
from typing import Any

from meta_client.errors import MetaRequestError, MetaRetryExhaustedError

INFRA = "infra_fail"
QUALITY = "quality_fail"
PASS = "pass"

_TIMEOUT = re.compile(r"timeout|timed out|RetryExhausted|connection (reset|error)|429|502|503|504", re.I)


def is_infra_error(exc: BaseException | None, message: str | None = None) -> bool:
    if isinstance(exc, (TimeoutError, MetaRetryExhaustedError, ConnectionError, OSError)):
        return True
    if isinstance(exc, MetaRequestError) and (exc.status == 429 or exc.status >= 500):
        return True
    text = message or (str(exc) if exc is not None else "")
    return bool(text and _TIMEOUT.search(text))


def classify_result(
    *,
    ok: bool | None,
    error: str | None = None,
    exc: BaseException | None = None,
    wall_s: float | None = None,
    run_timeout_s: float | None = None,
    skipped: bool = False,
) -> str:
    if skipped:
        return "skipped"
    if run_timeout_s is not None and wall_s is not None and wall_s >= run_timeout_s:
        return INFRA
    if is_infra_error(exc, error):
        return INFRA
    if ok:
        return PASS
    return QUALITY
