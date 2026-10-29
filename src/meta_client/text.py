"""Muse Spark over the Responses API: plain text, and JSON constrained by a schema.

Request shape from https://dev.meta.ai/docs/quickstart (input, reasoning.effort) and
https://dev.meta.ai/docs/structured-output (text.format for the Responses API).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from .client import MetaClient
from .errors import MetaResponseError
from .media import ImageInput
from .pricing import text_cost_usd


@dataclass(frozen=True)
class TextResult:
    text: str
    response_id: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class StructuredResult:
    data: dict[str, Any]
    text: str
    response_id: str | None
    raw: dict[str, Any]


def build_input(prompt: str, images: Sequence[ImageInput] = ()) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    content.extend({"type": "input_image", "image_url": img.data_url} for img in images)
    return [{"role": "user", "content": content}]


def extract_output_text(payload: dict[str, Any], *, allow_empty: bool = False) -> str:
    """Join the output_text parts of the assistant message. Raise on refusal or incomplete output.

    `allow_empty=True` is for SAM, where zero matches is a valid completed response with empty text.
    """
    status = payload.get("status")
    if status not in (None, "completed"):
        reason = (payload.get("incomplete_details") or {}).get("reason")
        raise MetaResponseError(f"response status={status!r} reason={reason!r}")
    texts: list[str] = []
    refusal: str | None = None
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for part in item.get("content", []):
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text":
                texts.append(str(part.get("text", "")))
            elif part.get("type") == "refusal":
                refusal = str(part.get("refusal") or "refused")
    if not texts and refusal is not None:
        raise MetaResponseError(f"model refused: {refusal}")
    if not texts and not allow_empty:
        raise MetaResponseError("response had no output_text")
    return "".join(texts)


def text_usage_fields(model: str, payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") or {}
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cached = int((usage.get("input_tokens_details") or {}).get("cached_tokens") or 0)
    reasoning = int((usage.get("output_tokens_details") or {}).get("reasoning_tokens") or 0)
    return {
        "input_tokens": input_tokens,
        "cached_tokens": cached,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning,
        "est_cost_usd": text_cost_usd(
            model,
            input_tokens=input_tokens,
            cached_tokens=cached,
            output_tokens=output_tokens,
        ),
    }


class MuseSpark:
    def __init__(self, client: MetaClient, model: str | None = None) -> None:
        self._client = client
        self.model = model or client.settings.text_model

    def _post(self, body: dict[str, Any], op: str) -> dict[str, Any]:
        model = self.model
        return self._client.post_json(
            "responses",
            {"model": model, **body},
            op=op,
            model=model,
            usage_fn=lambda payload: text_usage_fields(model, payload),
        )

    def generate(
        self,
        prompt: str,
        *,
        images: Sequence[ImageInput] = (),
        reasoning_effort: str | None = None,
    ) -> TextResult:
        body: dict[str, Any] = {"input": build_input(prompt, images)}
        if reasoning_effort is not None:
            body["reasoning"] = {"effort": reasoning_effort}
        payload = self._post(body, op="text.generate")
        return TextResult(
            text=extract_output_text(payload),
            response_id=payload.get("id"),
            raw=payload,
        )

    def generate_structured(
        self,
        prompt: str,
        *,
        schema: dict[str, Any],
        schema_name: str,
        images: Sequence[ImageInput] = (),
        reasoning_effort: str | None = None,
    ) -> StructuredResult:
        body: dict[str, Any] = {
            "input": build_input(prompt, images),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        if reasoning_effort is not None:
            body["reasoning"] = {"effort": reasoning_effort}
        payload = self._post(body, op="text.structured")
        text = extract_output_text(payload)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise MetaResponseError(f"structured output was not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise MetaResponseError("structured output was JSON but not an object")
        return StructuredResult(data=data, text=text, response_id=payload.get("id"), raw=payload)
