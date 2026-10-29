"""Thin, typed adapters for Meta Model API: Muse Spark, Muse Image, SAM 3.1.

Every Meta call in this repo goes through this package. See METAUSE.md for which
model does what and why it is needed.
"""

from .client import MetaClient
from .config import MetaSettings, load_settings
from .errors import (
    MetaAuthError,
    MetaConfigError,
    MetaError,
    MetaRequestError,
    MetaResponseError,
    MetaRetryExhaustedError,
)
from .images import GeneratedImage, MuseImage
from .media import ImageInput, image_input_from_bytes, image_input_from_path
from .segmentation import MetaSam, SamObject, SamResult
from .text import MuseSpark, StructuredResult, TextResult
from .usage import CallStats, UsageLog

__all__ = [
    "CallStats",
    "GeneratedImage",
    "ImageInput",
    "MetaAuthError",
    "MetaClient",
    "MetaConfigError",
    "MetaError",
    "MetaRequestError",
    "MetaResponseError",
    "MetaRetryExhaustedError",
    "MetaSam",
    "MetaSettings",
    "MuseImage",
    "MuseSpark",
    "SamObject",
    "SamResult",
    "StructuredResult",
    "TextResult",
    "UsageLog",
    "image_input_from_bytes",
    "image_input_from_path",
    "load_settings",
]
