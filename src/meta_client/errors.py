"""Typed errors raised by the Meta adapters."""

from __future__ import annotations


class MetaError(Exception):
    """Base class for every error raised by `meta_client`."""


class MetaConfigError(MetaError):
    """Settings are missing or invalid. Raised before any network call."""


class MetaRequestError(MetaError):
    """The API rejected the request (4xx). Permanent for that request: never retried."""

    def __init__(
        self,
        status: int,
        message: str,
        *,
        code: str | None = None,
        param: str | None = None,
    ) -> None:
        self.status = status
        self.code = code
        self.param = param
        detail = f"HTTP {status}"
        if code:
            detail += f" {code}"
        if param:
            detail += f" (param={param})"
        super().__init__(f"{detail}: {message}")


class MetaAuthError(MetaRequestError):
    """401/403: the key is missing, wrong, or not allowed for this model."""


class MetaRetryExhaustedError(MetaError):
    """Retryable failures (429/502/503/504, timeouts, connection drops) kept happening."""

    def __init__(self, attempts: int, last: str) -> None:
        self.attempts = attempts
        super().__init__(f"gave up after {attempts} attempts; last failure: {last}")


class MetaResponseError(MetaError):
    """HTTP 200 but the body is not what we can use (refusal, incomplete, bad JSON, bad shape)."""
