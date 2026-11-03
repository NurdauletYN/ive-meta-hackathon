"""MuseSparkPilot: wraps src/meta_client Muse Spark (model ID unchanged)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from meta_client import MetaClient, MuseSpark, load_settings
from meta_client.pricing import text_cost_usd
from meta_client.text import text_usage_fields

from .protocol import Usage


class MuseSparkPilot:
    name = "muse"

    def __init__(self, client: MetaClient | None = None) -> None:
        if client is None:
            settings = replace(load_settings(), usage_log=None)
            client = MetaClient(settings)
        self._client = client
        self._spark = MuseSpark(client)
        self.model = self._spark.model

    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        tag: str,
    ) -> tuple[dict[str, Any], Usage]:
        # Stable prefix first (system), variable content last (user) for prompt-cache hits.
        prompt = system + "\n\n" + user
        schema_name = "".join(ch for ch in tag.title() if ch.isalnum()) or "Payload"
        result = self._spark.generate_structured(prompt, schema=schema, schema_name=schema_name)
        fields = text_usage_fields(self.model, result.raw)
        last = self._client.usage.records[-1] if self._client.usage.records else None
        usage = Usage(
            input_tokens=int(fields.get("input_tokens") or 0),
            cached_tokens=int(fields.get("cached_tokens") or 0),
            output_tokens=int(fields.get("output_tokens") or 0),
            latency_ms=last.latency_ms if last else 0.0,
            est_cost_usd=fields.get("est_cost_usd")
            if fields.get("est_cost_usd") is not None
            else text_cost_usd(
                self.model,
                input_tokens=int(fields.get("input_tokens") or 0),
                cached_tokens=int(fields.get("cached_tokens") or 0),
                output_tokens=int(fields.get("output_tokens") or 0),
            ),
        )
        return result.data, usage
