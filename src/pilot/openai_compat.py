"""OpenAI-compatible chat completions (Baseten Muse Spark Open or any other model).

No live calls without an API key. Request shape: Chat Completions + json_schema
response_format (same structured-output flag as Meta's Chat Completions docs).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import httpx

from meta_client.errors import MetaAuthError, MetaRequestError, MetaResponseError
from meta_client.pricing import text_cost_usd

from .protocol import Usage


class OpenAICompatPilot:
    name = "openai_compat"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_s: float = 180.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key.strip():
            raise MetaAuthError(401, "OpenAI-compatible API key is empty; no live call made")
        self.model = model
        self._http = httpx.Client(
            base_url=base_url.rstrip("/") + "/",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=timeout_s,
            transport=transport,
        )

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        tag: str,
    ) -> tuple[dict[str, Any], Usage]:
        schema_name = "".join(ch for ch in tag.title() if ch.isalnum()) or "Payload"
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            },
        }
        started = time.perf_counter()
        resp = self._http.post("chat/completions", json=body)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        if resp.status_code in (401, 403):
            raise MetaAuthError(resp.status_code, resp.text[:300])
        if resp.status_code >= 400:
            raise MetaRequestError(resp.status_code, resp.text[:300])
        payload = resp.json()
        try:
            text = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MetaResponseError("chat completion missing choices[0].message.content") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MetaResponseError(f"completion was not JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise MetaResponseError("completion JSON was not an object")
        usage_block = payload.get("usage") or {}
        input_tokens = int(usage_block.get("prompt_tokens") or usage_block.get("input_tokens") or 0)
        output_tokens = int(usage_block.get("completion_tokens") or usage_block.get("output_tokens") or 0)
        cached = int((usage_block.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        return data, Usage(
            input_tokens=input_tokens,
            cached_tokens=cached,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            est_cost_usd=text_cost_usd(
                self.model, input_tokens=input_tokens, cached_tokens=cached, output_tokens=output_tokens
            ),
        )


def from_env(
    *,
    base_url_env: str = "OPENAI_COMPAT_BASE_URL",
    api_key_env: str = "OPENAI_COMPAT_API_KEY",
    model: str = "meta-models/muse-spark-open-1026",
) -> OpenAICompatPilot:
    base_url = os.environ.get(base_url_env, "").strip()
    api_key = os.environ.get(api_key_env, "").strip()
    if not base_url or not api_key:
        raise MetaAuthError(
            401,
            f"{base_url_env} and {api_key_env} must both be set; refusing to call the network",
        )
    return OpenAICompatPilot(base_url=base_url, model=model, api_key=api_key)
