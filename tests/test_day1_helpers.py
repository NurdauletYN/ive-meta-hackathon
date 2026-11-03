"""Offline tests for the Day 1 helpers: validator, overlay placement, sketch determinism."""

from __future__ import annotations

import hashlib
import io
import json
import random

import pytest
from file_ops import EXPECTED_OPS, FILE_OPS_SCHEMA, FileOp, check_plan
from make_samples import BUILDERS, EXPECTED, SAMPLES_DIR, SEED
from overlay import mask_to_image, paint_mask
from PIL import Image

from meta_client import SamObject


def _plan(ops: list[dict]) -> dict:
    return {"operations": ops}


def _expected_ops() -> list[dict]:
    return [
        {"op": "patch", "path": "lib/main.dart", "content": None, "find": "'Hello'", "replace": "'Welcome'"},
        {"op": "write", "path": "lib/widgets/card.dart", "content": "class Card {}", "find": None, "replace": None},
        {"op": "delete", "path": "lib/old_screen.dart", "content": None, "find": None, "replace": None},
    ]


def test_expected_plan_passes_schema_and_match() -> None:
    assert check_plan(_plan(_expected_ops())) == (True, True, [])


def test_missing_operation_is_reported() -> None:
    schema_ok, match, problems = check_plan(_plan(_expected_ops()[:2]))
    assert schema_ok is True and match is False
    assert "missing delete lib/old_screen.dart" in problems


def test_invalid_shape_is_schema_failure() -> None:
    schema_ok, match, problems = check_plan({"operations": [{"op": "rename", "path": "a.dart"}]})
    assert (schema_ok, match) == (False, False)
    assert problems


def test_empty_plan_is_invalid() -> None:
    assert check_plan({"operations": []})[0] is False


@pytest.mark.parametrize(
    "bad",
    [
        {"op": "write", "path": "/etc/passwd", "content": "x"},
        {"op": "write", "path": "../outside.dart", "content": "x"},
        {"op": "write", "path": "lib\\win.dart", "content": "x"},
        {"op": "write", "path": "lib/a.dart", "content": None},
        {"op": "patch", "path": "lib/a.dart", "find": "a", "replace": None},
        {"op": "delete", "path": "lib/a.dart", "content": "x"},
    ],
)
def test_file_op_rules_reject_unsafe_or_incomplete_ops(bad: dict) -> None:
    with pytest.raises(ValueError):
        FileOp.model_validate({"find": None, "replace": None, **bad})


def test_schema_is_strict_about_extra_keys_and_required_fields() -> None:
    item = FILE_OPS_SCHEMA["properties"]["operations"]["items"]
    assert item["additionalProperties"] is False
    assert set(item["required"]) == set(item["properties"])
    assert FILE_OPS_SCHEMA["additionalProperties"] is False


def test_expected_ops_constant_matches_prompt_intent() -> None:
    assert ("delete", "lib/old_screen.dart") in EXPECTED_OPS and len(EXPECTED_OPS) == 3


def test_paint_mask_lands_on_its_box_not_the_origin() -> None:
    obj = SamObject(
        object_id="0",
        left=3,
        top=1,
        right=5,
        bottom=3,
        confidence=None,
        mask_width=2,
        mask_height=2,
        mask=bytes([1, 1, 1, 1]),
    )
    canvas = Image.new("RGB", (8, 6), (0, 0, 0))
    paint_mask(canvas, obj, (255, 0, 0), alpha=1.0)
    assert canvas.getpixel((3, 1)) == (255, 0, 0)
    assert canvas.getpixel((4, 2)) == (255, 0, 0)
    assert canvas.getpixel((0, 0)) == (0, 0, 0)  # origin untouched
    assert canvas.getpixel((5, 1)) == (0, 0, 0)  # just outside the box


def test_mask_length_mismatch_is_rejected() -> None:
    obj = SamObject(
        object_id="0",
        left=0,
        top=0,
        right=2,
        bottom=2,
        confidence=None,
        mask_width=2,
        mask_height=2,
        mask=bytes([1, 0, 1]),
    )
    with pytest.raises(ValueError, match="expected 2x2"):
        mask_to_image(obj)


def _digest(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return hashlib.sha256(buf.getvalue()).hexdigest()


def test_sketch_generation_is_deterministic() -> None:
    for index, (name, build) in enumerate(BUILDERS.items()):
        first = build(random.Random(SEED + index))
        second = build(random.Random(SEED + index))
        assert _digest(first) == _digest(second), name


def test_committed_samples_match_manifest() -> None:
    manifest = json.loads((SAMPLES_DIR / "manifest.json").read_text(encoding="utf-8"))["sketches"]
    assert {k.removesuffix(".png") for k in manifest} == set(EXPECTED)
    for name, meta in manifest.items():
        assert meta["expected_counts"] == EXPECTED[name.removesuffix(".png")]
        assert (SAMPLES_DIR / name).exists()

