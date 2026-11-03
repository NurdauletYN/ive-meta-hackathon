"""Settings for the Meta Model API adapters, read from environment variables.

Standard mode only: Contributor-mode model IDs (suffix `-contributor`) are rejected
on purpose, because Contributor mode lets Meta train on our content.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from .errors import MetaConfigError

DEFAULT_BASE_URL = "https://api.meta.ai/v1"
DEFAULT_TEXT_MODEL = "muse-spark-1.3"
DEFAULT_IMAGE_MODEL = "muse-image-1.0"


@dataclass(frozen=True)
class MetaSettings:
    api_key: str = field(repr=False)  # never printed, never logged
    base_url: str = DEFAULT_BASE_URL
    text_model: str = DEFAULT_TEXT_MODEL
    image_model: str = DEFAULT_IMAGE_MODEL
    timeout_s: float = 90.0
    max_retries: int = 2
    usage_log: Path | None = None

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise MetaConfigError("META_API_KEY is empty.")
        if not (self.base_url.startswith("https://") or self.base_url.startswith("http://localhost")):
            raise MetaConfigError(f"META_BASE_URL must be https (got {self.base_url!r}).")
        for label, model in (
            ("META_MODEL_TEXT", self.text_model),
            ("META_MODEL_IMAGE", self.image_model),
        ):
            if model.endswith("-contributor"):
                raise MetaConfigError(
                    f"{label}={model!r} is a Contributor-mode model. This project uses Standard mode only."
                )
        if self.timeout_s <= 0:
            raise MetaConfigError("timeout_s must be positive.")
        if self.max_retries < 0:
            raise MetaConfigError("max_retries must be >= 0.")

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> MetaSettings:
        env = os.environ if environ is None else environ
        api_key = env.get("META_API_KEY", "").strip()
        if not api_key:
            raise MetaConfigError(
                "META_API_KEY is not set. Copy .env.example to .env and put your key in it."
            )
        usage_log_raw = env.get("META_USAGE_LOG", "").strip()
        timeout_raw = env.get("META_TIMEOUT_S", "").strip()
        retries_raw = env.get("META_MAX_RETRIES", "").strip()
        return cls(
            api_key=api_key,
            base_url=env.get("META_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/"),
            text_model=env.get("META_MODEL_TEXT", DEFAULT_TEXT_MODEL).strip(),
            image_model=env.get("META_MODEL_IMAGE", DEFAULT_IMAGE_MODEL).strip(),
            timeout_s=float(timeout_raw) if timeout_raw else 90.0,
            max_retries=int(retries_raw) if retries_raw else 2,
            usage_log=Path(usage_log_raw) if usage_log_raw else None,
        )


def load_settings() -> MetaSettings:
    """Load `.env` from the current directory tree (if present), then read the environment."""
    load_dotenv(find_dotenv(usecwd=True), override=False)
    return MetaSettings.from_env()
