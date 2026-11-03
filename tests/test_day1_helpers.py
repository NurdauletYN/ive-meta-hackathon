"""Offline tests for Day 1 file-operations helper (still used by harness guard schema)."""

from __future__ import annotations

import pytest
from file_ops import EXPECTED_OPS, FILE_OPS_SCHEMA, FileOp, check_plan


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


@pytest.mark.parametrize(
    "bad",
    [
        {"op": "write", "path": "/etc/passwd", "content": "x"},
        {"op": "write", "path": "../outside.dart", "content": "x"},
    ],
)
def test_file_op_rules_reject_unsafe_paths(bad: dict) -> None:
    with pytest.raises(ValueError):
        FileOp.model_validate({"find": None, "replace": None, **bad})


def test_schema_is_strict() -> None:
    item = FILE_OPS_SCHEMA["properties"]["operations"]["items"]
    assert item["additionalProperties"] is False
    assert len(EXPECTED_OPS) == 3
