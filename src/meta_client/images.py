"""Muse Image (`muse-image-1.0`) via the single-shot images endpoint.

Request fields from https://dev.meta.ai/docs/guides/image-generation (the page that
documents /v1/images/generations): model, prompt, n (1-10), size ("WxH", aspect ratio
only), output_format, response_format="b64_json". The docs say the returned pixel size
can differ from `size`, so we report the decoded dimensions instead of assuming them.
"""

from __future__ import annotations

import base64
import binascii
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .client import MetaClient
from .errors import MetaResponseError
from .pricing import image_cost_usd

SUPPORTED_OUTPUT_FORMATS = frozenset({"png", "jpeg", "webp"})
_SIZE_RE = re.compile(r"^\d+x\d+$")
MAX_N = 10


@dataclass(frozen=True)
class GeneratedImage:
    data: bytes
    output_format: str
    width: int | None
    height: int | None


def _decoded_size(data: bytes) -> tuple[int, int] | tuple[None, None]:
    try:
        with Image.open(io.BytesIO(data)) as img:
            width, height = img.size
            return width, height
    except (UnidentifiedImageError, OSError):
        return None, None


class MuseImage:
    def __init__(self, client: MetaClient, model: str | None = None) -> None:
        self._client = client
        self.model = model or client.settings.image_model

    def generate(
        self,
        prompt: str,
        *,
        size: str = "1024x1024",
        output_format: str = "png",
        n: int = 1,
    ) -> list[GeneratedImage]:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")
        if not 1 <= n <= MAX_N:
            raise ValueError(f"n must be between 1 and {MAX_N} (got {n})")
        if not _SIZE_RE.match(size):
            raise ValueError(f"size must look like '1024x1024' (got {size!r})")
        if output_format not in SUPPORTED_OUTPUT_FORMATS:
            raise ValueError(f"output_format must be one of {sorted(SUPPORTED_OUTPUT_FORMATS)}")

        model = self.model
        body: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size,
            "output_format": output_format,
            "response_format": "b64_json",
        }
        payload = self._client.post_json(
            "images/generations",
            body,
            op="image.generate",
            model=model,
            usage_fn=lambda p: _image_usage_fields(model, p),
        )
        items = payload.get("data")
        if not isinstance(items, list) or not items:
            raise MetaResponseError("image response had no data entries")

        images: list[GeneratedImage] = []
        for item in items:
            b64 = item.get("b64_json") if isinstance(item, dict) else None
            if not isinstance(b64, str) or not b64:
                raise MetaResponseError("image response entry had no b64_json")
            try:
                data = base64.b64decode(b64, validate=True)
            except binascii.Error as exc:
                raise MetaResponseError("image response b64_json was not valid base64") from exc
            width, height = _decoded_size(data)
            images.append(
                GeneratedImage(
                    data=data,
                    output_format=str(payload.get("output_format") or output_format),
                    width=width,
                    height=height,
                )
            )
        return images


def _image_usage_fields(model: str, payload: dict[str, Any]) -> dict[str, Any]:
    count = len(payload.get("data") or [])
    return {"images": count, "est_cost_usd": image_cost_usd(model, count)}


def resize_lanczos_to_square(data: bytes, size: int = 1024) -> tuple[bytes, int, int]:
    """Resize decoded image bytes to ``size×size`` with Lanczos. Returns PNG bytes and dimensions."""
    with Image.open(io.BytesIO(data)) as img:
        rgb = img.convert("RGB")
        resized = rgb.resize((size, size), Image.Resampling.LANCZOS)
        out = io.BytesIO()
        resized.save(out, format="PNG", optimize=True)
        return out.getvalue(), size, size


def save_png_pair(
    raw_path: Path,
    raw_bytes: bytes,
    *,
    resized_path: Path | None = None,
    target_size: int = 1024,
) -> tuple[Path, Path | None]:
    """Write the raw API bytes, then optionally write a Lanczos-resized PNG beside it."""
    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_bytes(raw_bytes)
    if resized_path is None:
        return raw_path, None
    resized_bytes, _, _ = resize_lanczos_to_square(raw_bytes, target_size)
    resized_path = Path(resized_path)
    resized_path.write_bytes(resized_bytes)
    return raw_path, resized_path
