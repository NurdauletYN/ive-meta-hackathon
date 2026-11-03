"""Image inputs for Meta calls: base64 data URLs (documented for Muse Spark, SAM and Muse Image)."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class UnsupportedImageError(ValueError):
    """The file type is not one the documented image inputs accept."""


@dataclass(frozen=True)
class ImageInput:
    data_url: str
    mime: str
    num_bytes: int


def image_input_from_bytes(data: bytes, mime: str) -> ImageInput:
    if mime not in _MIME_BY_SUFFIX.values():
        raise UnsupportedImageError(f"unsupported image mime type: {mime!r}")
    encoded = base64.b64encode(data).decode("ascii")
    return ImageInput(data_url=f"data:{mime};base64,{encoded}", mime=mime, num_bytes=len(data))


def image_input_from_path(path: Path) -> ImageInput:
    mime = _MIME_BY_SUFFIX.get(path.suffix.lower())
    if mime is None:
        raise UnsupportedImageError(f"unsupported image type for {path.name}: {path.suffix!r}")
    return image_input_from_bytes(path.read_bytes(), mime)
