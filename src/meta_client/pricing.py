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


# Muse Spark 1.3 Standard: https://dev.meta.ai/docs/pricing-rate-limits (read 2026-11-03).
# Muse Spark Open on Baseten: same $/1M as Spark Standard on Baseten's public model list
# (www.baseten.co/pricing, observed 2026-11-03). Official Meta Model API page does not
# list the open-weight id; unknown ids still return None.
_SPARK_STANDARD = TokenPrice(input_per_m=1.25, cached_input_per_m=0.15, output_per_m=4.25)
TEXT_PRICES: dict[str, TokenPrice] = {
    "muse-spark-1.3": _SPARK_STANDARD,
    "muse-spark-open": _SPARK_STANDARD,
    "meta-models/muse-spark-open": _SPARK_STANDARD,
    "meta-models/muse-spark-open-1026": _SPARK_STANDARD,
}

MUSE_IMAGE_PRICE_PER_IMAGE: dict[str, float] = {
    "muse-image-1.0": 0.01,  # flat per generated image
}


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
