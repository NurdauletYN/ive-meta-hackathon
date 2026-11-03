"""Offline tests for meta_client: no network, no API key. Covers success and failure paths.

Live behaviour is checked by scripts/day1/ (smoke tests), not here.
"""

from __future__ import annotations

import base64
import io
import json
import random
from pathlib import Path
from typing import Any

import httpx
import pytest
from PIL import Image

from meta_client import (
    MetaAuthError,
    MetaClient,
    MetaConfigError,
    MetaRequestError,
    MetaResponseError,
    MetaRetryExhaustedError,
    MetaSettings,
    MuseImage,
    MuseSpark,
    UsageLog,
    image_input_from_bytes,
)
from meta_client.pricing import text_cost_usd


def _settings(**overrides: Any) -> MetaSettings:
    base = {"api_key": "test-key-not-real", "usage_log": None}
    base.update(overrides)
    return MetaSettings(**base)


def _client(handler, *, sleeps: list[float] | None = None, **settings: Any) -> MetaClient:
    sleeps_list = sleeps if sleeps is not None else []
    return MetaClient(
        _settings(**settings),
        transport=httpx.MockTransport(handler),
        sleep=sleeps_list.append,
        rng=random.Random(0),
        usage=UsageLog(None),
    )


def _text_ok(text: str = "hello", *, input_tokens: int = 100, output_tokens: int = 20) -> dict[str, Any]:
    return {
        "id": "resp_1",
        "status": "completed",
        "output": [
            {"type": "reasoning", "summary": []},
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text, "annotations": []}],
            },
        ],
        "usage": {
            "input_tokens": input_tokens,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": output_tokens,
            "output_tokens_details": {"reasoning_tokens": 5},
            "total_tokens": input_tokens + output_tokens,
        },
    }


def _tiny_png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


# ---------- config ----------


def test_settings_require_api_key() -> None:
    with pytest.raises(MetaConfigError, match="META_API_KEY is not set"):
        MetaSettings.from_env({})


def test_settings_reject_contributor_model() -> None:
    with pytest.raises(MetaConfigError, match="Standard mode only"):
        MetaSettings.from_env({"META_API_KEY": "k", "META_MODEL_TEXT": "muse-spark-1.3-contributor"})


def test_settings_default_models_are_standard_mode() -> None:
    s = MetaSettings.from_env({"META_API_KEY": "k"})
    assert s.text_model == "muse-spark-1.3"
    assert s.image_model == "muse-image-1.0"
    assert not s.text_model.endswith("-contributor")


def test_settings_repr_hides_key() -> None:
    assert "secret-value" not in repr(MetaSettings.from_env({"META_API_KEY": "secret-value"}))


def test_settings_reject_plain_http_base_url() -> None:
    with pytest.raises(MetaConfigError, match="must be https"):
        MetaSettings.from_env({"META_API_KEY": "k", "META_BASE_URL": "http://example.com/v1"})


# ---------- retries and error mapping ----------


def test_retries_503_then_succeeds_and_backs_off() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, json={"error": {"type": "server_error", "message": "busy"}})
        return httpx.Response(200, json=_text_ok("ok"))

    sleeps: list[float] = []
    client = _client(handler, sleeps=sleeps)
    result = MuseSpark(client).generate("hi")
    assert result.text == "ok"
    assert calls["n"] == 2
    assert len(sleeps) == 1 and 0.5 <= sleeps[0] <= 0.5 * 1.25
    assert client.usage.records[-1].ok and client.usage.records[-1].attempts == 2


def test_429_honours_retry_after() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"}, json={"error": {"message": "slow down"}})
        return httpx.Response(200, json=_text_ok("ok"))

    sleeps: list[float] = []
    MuseSpark(_client(handler, sleeps=sleeps)).generate("hi")
    assert len(sleeps) == 1
    assert sleeps[0] >= 7.0  # Retry-After is a floor, not a suggestion


def test_400_is_not_retried_and_keeps_code_and_param() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(
            400,
            json={"error": {"type": "invalid_request_error", "param": "n", "message": "`n` The number must be `<= 10`."}},
        )

    client = _client(handler)
    with pytest.raises(MetaRequestError) as info:
        MuseImage(client).generate("a fox", n=1)
    assert calls["n"] == 1
    assert info.value.status == 400
    assert info.value.param == "n"
    assert client.usage.records[-1].ok is False


def test_401_maps_to_auth_error_without_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401, json={"error": {"code": "invalid_api_key", "message": "bad key"}})

    with pytest.raises(MetaAuthError, match="invalid_api_key"):
        MuseSpark(_client(handler)).generate("hi")
    assert calls["n"] == 1


def test_500_is_not_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": {"message": "internal"}})

    with pytest.raises(MetaRequestError):
        MuseSpark(_client(handler)).generate("hi")
    assert calls["n"] == 1


def test_retries_exhausted_raises_and_logs_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"message": "down"}})

    client = _client(handler, max_retries=2)
    with pytest.raises(MetaRetryExhaustedError) as info:
        MuseSpark(client).generate("hi")
    assert info.value.attempts == 3  # first try + 2 retries
    last = client.usage.records[-1]
    assert last.ok is False and last.attempts == 3 and last.status == 503


def test_timeouts_are_retried_then_raise() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(MetaRetryExhaustedError, match="timeout"):
        MuseSpark(_client(handler, max_retries=1)).generate("hi")


def test_non_json_200_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html>proxy</html>")

    with pytest.raises(MetaResponseError, match="not JSON"):
        MuseSpark(_client(handler)).generate("hi")


def test_request_carries_bearer_auth_and_model() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        seen["url"] = str(request.url)
        return httpx.Response(200, json=_text_ok("ok"))

    MuseSpark(_client(handler)).generate("hi")
    assert seen["auth"] == "Bearer test-key-not-real"
    assert seen["url"] == "https://api.meta.ai/v1/responses"
    assert seen["body"]["model"] == "muse-spark-1.3"
    assert seen["body"]["input"][0]["content"][0] == {"type": "input_text", "text": "hi"}


# ---------- usage logging and pricing ----------


def test_usage_log_writes_jsonl_with_tokens_and_cost(tmp_path: Path) -> None:
    log_path = tmp_path / "usage.jsonl"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_text_ok("ok", input_tokens=1000, output_tokens=200))

    client = MetaClient(
        _settings(usage_log=log_path),
        transport=httpx.MockTransport(handler),
        sleep=lambda _s: None,
        usage=None,
    )
    MuseSpark(client).generate("hi")
    line = json.loads(log_path.read_text().splitlines()[0])
    assert line["op"] == "text.generate" and line["ok"] is True
    assert line["input_tokens"] == 1000 and line["output_tokens"] == 200
    assert line["est_cost_usd"] == pytest.approx((1000 * 1.25 + 200 * 4.25) / 1e6)
    assert line["latency_ms"] >= 0


def test_text_cost_uses_cached_rate_for_cached_tokens() -> None:
    cost = text_cost_usd("muse-spark-1.3", input_tokens=1000, cached_tokens=600, output_tokens=0)
    assert cost == pytest.approx((400 * 1.25 + 600 * 0.15) / 1e6)


def test_unknown_model_has_no_guessed_price() -> None:
    assert text_cost_usd("some-future-model", input_tokens=10, cached_tokens=0, output_tokens=10) is None


# ---------- Muse Spark ----------


def test_structured_output_sends_text_format_and_parses() -> None:
    seen: dict[str, Any] = {}
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
        "additionalProperties": False,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=_text_ok('{"ok": true}'))

    result = MuseSpark(_client(handler)).generate_structured("is it?", schema=schema, schema_name="Check")
    assert result.data == {"ok": True}
    fmt = seen["body"]["text"]["format"]
    assert fmt == {"type": "json_schema", "name": "Check", "schema": schema, "strict": True}


def test_structured_output_invalid_json_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_text_ok("not json at all"))

    with pytest.raises(MetaResponseError, match="not valid JSON"):
        MuseSpark(_client(handler)).generate_structured("x", schema={"type": "object"}, schema_name="S")


def test_refusal_is_a_response_error() -> None:
    body = {
        "id": "resp_r",
        "status": "completed",
        "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(MetaResponseError, match="refused"):
        MuseSpark(_client(handler)).generate("x")


def test_incomplete_status_is_a_response_error() -> None:
    body = {"id": "resp_i", "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}, "output": []}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(MetaResponseError, match="max_output_tokens"):
        MuseSpark(_client(handler)).generate("x")


def test_image_input_is_sent_as_data_url() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=_text_ok("a button"))

    img = image_input_from_bytes(_tiny_png(), "image/png")
    MuseSpark(_client(handler)).generate("what is this?", images=[img])
    part = seen["body"]["input"][0]["content"][1]
    assert part["type"] == "input_image" and part["image_url"].startswith("data:image/png;base64,")


def test_unsupported_image_mime_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported image mime"):
        image_input_from_bytes(b"GIF89a", "image/gif")


# ---------- Muse Image ----------


def test_image_generate_decodes_bytes_and_reports_size() -> None:
    png = _tiny_png()
    b64 = base64.b64encode(png).decode()

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["response_format"] == "b64_json" and body["size"] == "1024x1024"
        return httpx.Response(200, json={"created": 1, "data": [{"b64_json": b64}], "output_format": "png"})

    client = _client(handler)
    (img,) = MuseImage(client).generate("an icon")
    assert img.data == png and img.output_format == "png"
    assert (img.width, img.height) == (8, 8)  # actual decoded size, not the requested one
    assert client.usage.records[-1].images == 1
    assert client.usage.records[-1].est_cost_usd == pytest.approx(0.01)


def test_image_generate_missing_data_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"created": 1, "data": []})

    with pytest.raises(MetaResponseError, match="no data"):
        MuseImage(_client(handler)).generate("an icon")


def test_image_generate_bad_base64_is_a_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": [{"b64_json": "!!!not-base64!!!"}]})

    with pytest.raises(MetaResponseError, match="base64"):
        MuseImage(_client(handler)).generate("an icon")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n": 0}, "n must be between"),
        ({"n": 11}, "n must be between"),
        ({"size": "square"}, "size must look like"),
        ({"output_format": "gif"}, "output_format must be one of"),
    ],
)
def test_image_generate_validates_inputs_before_network(kwargs: dict[str, Any], message: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover - must not be reached
        raise AssertionError("network must not be called")

    with pytest.raises(ValueError, match=message):
        MuseImage(_client(handler)).generate("an icon", **kwargs)


def test_resize_lanczos_produces_exact_square_png() -> None:
    from meta_client.images import resize_lanczos_to_square

    out, w, h = resize_lanczos_to_square(_tiny_png(), 1024)
    assert (w, h) == (1024, 1024)
    assert out.startswith(b"\x89PNG")
