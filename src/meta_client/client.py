"""HTTP transport for Meta Model API: auth, timeouts, retries with backoff, usage logging.

Retry policy (from https://dev.meta.ai/docs/pricing-rate-limits and the image docs):
- Retry 429, 502, 503, 504 with exponential backoff (0.5 s, doubling, capped at 30 s)
  plus jitter. A `Retry-After` header raises the wait to at least that value.
- Retry timeouts and connection errors too. A timed-out POST may still have run on
  the server, so generation calls can be billed twice; that is recorded in the usage log.
- Never retry other 4xx (400 is permanent for that request) and never retry 500
  (the image docs classify unclassified backend errors as 500).
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import Any

import httpx

from .config import MetaSettings
from .errors import MetaAuthError, MetaRequestError, MetaResponseError, MetaRetryExhaustedError
from .usage import CallStats, UsageLog

RETRYABLE_STATUS = frozenset({429, 502, 503, 504})
BASE_BACKOFF_S = 0.5
MAX_BACKOFF_S = 30.0

# Maps a successful JSON body to extra CallStats fields (tokens, images, est_cost_usd).
UsageFn = Callable[[dict[str, Any]], dict[str, Any]]


def _error_from_response(resp: httpx.Response) -> MetaRequestError:
    message = resp.text[:500]
    code: str | None = None
    param: str | None = None
    try:
        body = resp.json()
    except ValueError:
        body = None
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        err = body["error"]
        message = str(err.get("message") or message)
        code = err.get("code") or err.get("type")
        param = err.get("param")
    if resp.status_code in (401, 403):
        return MetaAuthError(resp.status_code, message, code=code, param=param)
    return MetaRequestError(resp.status_code, message, code=code, param=param)


def _retry_after_seconds(resp: httpx.Response) -> float | None:
    raw = resp.headers.get("retry-after")
    if not raw:
        return None
    try:
        return max(float(raw), 0.0)
    except ValueError:
        return None  # HTTP-date form is not used by the API docs; fall back to backoff


class MetaClient:
    def __init__(
        self,
        settings: MetaSettings,
        *,
        usage: UsageLog | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.settings = settings
        self.usage = usage if usage is not None else UsageLog(settings.usage_log)
        self._sleep = sleep
        self._rng = rng if rng is not None else random.Random()
        self._clock = clock
        self._http = httpx.Client(
            base_url=settings.base_url + "/",
            headers={
                "Authorization": f"Bearer {settings.api_key}",
                "Accept": "application/json",
            },
            timeout=settings.timeout_s,
            transport=transport,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> MetaClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def post_json(
        self,
        path: str,
        body: dict[str, Any],
        *,
        op: str,
        model: str,
        usage_fn: UsageFn | None = None,
    ) -> dict[str, Any]:
        """POST a JSON body and return the parsed JSON object. Raises a `MetaError` subclass on failure."""
        started = self._clock()
        attempts = 0
        while True:
            attempts += 1
            retry_after: float | None = None
            status: int | None = None
            try:
                resp = self._http.post(path, json=body)
            except httpx.TimeoutException as exc:
                failure = f"timeout: {exc}"
            except httpx.TransportError as exc:
                failure = f"transport: {exc}"
            else:
                status = resp.status_code
                if status < 400:
                    try:
                        payload = resp.json()
                    except ValueError as exc:
                        self._fail(op, model, path, status, attempts, started, "200 with non-JSON body")
                        raise MetaResponseError(f"{op}: 200 response was not JSON") from exc
                    if not isinstance(payload, dict):
                        self._fail(op, model, path, status, attempts, started, "200 with non-object body")
                        raise MetaResponseError(f"{op}: 200 response was not a JSON object")
                    extra = usage_fn(payload) if usage_fn is not None else {}
                    self.usage.write(
                        CallStats(
                            ts=CallStats.now_iso(),
                            op=op,
                            model=model,
                            path=path,
                            ok=True,
                            status=status,
                            attempts=attempts,
                            latency_ms=round((self._clock() - started) * 1000, 1),
                            **extra,
                        )
                    )
                    return payload

                error = _error_from_response(resp)
                if status not in RETRYABLE_STATUS:
                    self._fail(op, model, path, status, attempts, started, str(error))
                    raise error
                retry_after = _retry_after_seconds(resp)
                failure = f"HTTP {status}: {error}"

            if attempts > self.settings.max_retries:
                self._fail(op, model, path, status, attempts, started, failure)
                raise MetaRetryExhaustedError(attempts, failure)
            self._sleep(self._backoff(attempts, retry_after))

    def _backoff(self, attempt: int, retry_after: float | None) -> float:
        base = min(BASE_BACKOFF_S * (2 ** (attempt - 1)), MAX_BACKOFF_S)
        delay = base + self._rng.uniform(0, base * 0.25)
        if retry_after is not None:
            delay = max(delay, retry_after)
        return delay

    def _fail(
        self,
        op: str,
        model: str,
        path: str,
        status: int | None,
        attempts: int,
        started: float,
        error: str,
    ) -> None:
        self.usage.write(
            CallStats(
                ts=CallStats.now_iso(),
                op=op,
                model=model,
                path=path,
                ok=False,
                status=status,
                attempts=attempts,
                latency_ms=round((self._clock() - started) * 1000, 1),
                error=error[:500],
            )
        )
