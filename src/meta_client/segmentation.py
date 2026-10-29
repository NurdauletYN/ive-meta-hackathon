"""SAM 3.1 (`sam-3.1`) on an image: one concept per request, parsed with the official parser.

Request shape and output grammar: https://dev.meta.ai/docs/sam/segmenting and
https://dev.meta.ai/docs/sam/reading-segmentation. The grammar and mask decoding are
done by `meta-sam-parser` (official Meta package, SAM License), pinned in uv.lock.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from meta_sam_parser import (
    CompletedOutcome,
    IncompleteOutcome,
    SegmentationMaskRecord,
    decode_mask_to_raster,
    image_segmentation_format,
)

from .client import MetaClient
from .errors import MetaResponseError
from .media import ImageInput
from .pricing import sam_image_cost_usd
from .text import extract_output_text

_FORBIDDEN_IN_CONCEPT = (",", ";", "+", "\n")


@dataclass(frozen=True)
class SamObject:
    """One segmented object. Box is in source-image pixels, half-open: right = x2 + 1, bottom = y2 + 1."""

    object_id: str
    left: float
    top: float
    right: float
    bottom: float
    confidence: float | None
    mask_width: int
    mask_height: int
    mask: bytes = field(repr=False)  # row-major 0/1 raster, length mask_width * mask_height


@dataclass(frozen=True)
class SamResult:
    concept: str
    response_id: str | None
    raw_text: str
    objects: tuple[SamObject, ...]
    diagnostics: tuple[str, ...]

    @property
    def count(self) -> int:
        return len(self.objects)


def validate_concept(concept: str) -> str:
    """One short noun phrase per request. Lists and sentences return zero matches, so reject them early."""
    text = concept.strip()
    if not text:
        raise ValueError("concept must not be empty")
    for bad in _FORBIDDEN_IN_CONCEPT:
        if bad in text:
            raise ValueError(f"concept must be one noun phrase; {bad!r} is not allowed (got {concept!r})")
    return text


def parse_sam_text(raw_text: str, concept: str, response_id: str | None) -> SamResult:
    parser = image_segmentation_format().create_parser()
    parser.push(raw_text)
    finished = parser.finish(CompletedOutcome())
    result = finished.result
    if isinstance(result.outcome, IncompleteOutcome):
        raise MetaResponseError(f"SAM output incomplete: {result.outcome.reason} {result.outcome.detail or ''}")

    errors = [d for d in result.diagnostics if str(d.severity).lower() == "error"]
    if errors:
        first = errors[0]
        raise MetaResponseError(f"SAM output had a malformed line {first.line}: {first.code}: {first.message}")

    objects: list[SamObject] = []
    for record in result.records:
        if not isinstance(record, SegmentationMaskRecord):
            continue
        raster = decode_mask_to_raster(record.mask)
        objects.append(
            SamObject(
                object_id=record.object_id,
                left=record.bounds.left,
                top=record.bounds.top,
                right=record.bounds.right,
                bottom=record.bounds.bottom,
                confidence=record.confidence,
                mask_width=record.mask.width,
                mask_height=record.mask.height,
                mask=bytes(raster),
            )
        )
    return SamResult(
        concept=concept,
        response_id=response_id,
        raw_text=raw_text,
        objects=tuple(objects),
        diagnostics=tuple(f"{d.code}: {d.message}" for d in result.diagnostics),
    )


def _sam_usage_fields(_payload: dict[str, Any]) -> dict[str, Any]:
    return {"images": 1, "est_cost_usd": sam_image_cost_usd(1)}


class MetaSam:
    def __init__(self, client: MetaClient, model: str | None = None) -> None:
        self._client = client
        self.model = model or client.settings.segment_model

    def segment_image(
        self,
        image: ImageInput,
        concept: str,
        *,
        include_confidence: bool = False,
    ) -> SamResult:
        text = validate_concept(concept)
        body: dict[str, Any] = {
            "model": self.model,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": text},
                        {"type": "input_image", "image_url": image.data_url},
                    ],
                }
            ],
        }
        if include_confidence:
            body["metadata"] = {"include_confidence": "true"}
        payload = self._client.post_json(
            "responses",
            body,
            op="sam.segment_image",
            model=self.model,
            usage_fn=_sam_usage_fields,
        )
        raw_text = extract_output_text(payload, allow_empty=True)  # zero matches = empty lane
        return parse_sam_text(raw_text, text, payload.get("id"))
