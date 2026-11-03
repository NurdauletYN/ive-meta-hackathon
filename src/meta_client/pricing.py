"""Pay-as-you-go prices in USD, Standard mode only.

Source: https://dev.meta.ai/docs/pricing-rate-limits (read 2026-10-30).
Unknown models return None rather than a guessed price.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPrice:
    input_per_m: float
    cached_input_per_m: float
    output_per_m: float


# Muse Spark 1.3, Standard mode, per 1M tokens.
TEXT_PRICES: dict[str, TokenPrice] = {
    "muse-spark-1.3": TokenPrice(input_per_m=1.25, cached_input_per_m=0.15, output_per_m=4.25),
}

MUSE_IMAGE_PRICE_PER_IMAGE: dict[str, float] = {
    "muse-image-1.0": 0.01,  # flat per generated image
}

SAM_IMAGE_PRICE_PER_IMAGE = 2.50 / 1000  # $2.50 per 1,000 images
SAM_VIDEO_PRICE_PER_FRAME = 0.20 / 1000  # $0.20 per 1,000 frames (not used on Day 1)


def text_cost_usd(
    model: str,
    *,
    input_tokens: int,
    cached_tokens: int,
    output_tokens: int,
) -> float | None:
    """Cost of one token-priced call. `input_tokens` includes `cached_tokens` (OpenAI convention)."""
    price = TEXT_PRICES.get(model)
    if price is None:
        return None
    uncached = max(input_tokens - cached_tokens, 0)
    return (
        uncached * price.input_per_m
        + cached_tokens * price.cached_input_per_m
        + output_tokens * price.output_per_m
    ) / 1_000_000


def image_cost_usd(model: str, images: int) -> float | None:
    per_image = MUSE_IMAGE_PRICE_PER_IMAGE.get(model)
    return None if per_image is None else per_image * images


def sam_image_cost_usd(images: int) -> float:
    return SAM_IMAGE_PRICE_PER_IMAGE * images
