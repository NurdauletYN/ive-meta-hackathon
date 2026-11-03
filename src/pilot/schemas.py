"""JSON schemas for design directions, app spec, and file ops (strict, no extra keys)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

_FORBID = ConfigDict(extra="forbid")

COLOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "primary": {"type": "string", "description": "hex #RRGGBB"},
        "on_primary": {"type": "string"},
        "surface": {"type": "string"},
        "on_surface": {"type": "string"},
    },
    "required": ["primary", "on_primary", "surface", "on_surface"],
    "additionalProperties": False,
}

CONTRAST_PAIR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "foreground": {"type": "string"},
        "background": {"type": "string"},
    },
    "required": ["name", "foreground", "background"],
    "additionalProperties": False,
}

TOKENS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "colors": COLOR_SCHEMA,
        "contrast_pairs": {"type": "array", "items": CONTRAST_PAIR_SCHEMA},
        "corner_radius": {"type": "number"},
        "typography": {"type": "string", "enum": ["default", "compact", "expressive"]},
    },
    "required": ["colors", "contrast_pairs", "corner_radius", "typography"],
    "additionalProperties": False,
}

DIRECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "rationale": {"type": "string"},
        "tokens": TOKENS_SCHEMA,
    },
    "required": ["name", "rationale", "tokens"],
    "additionalProperties": False,
}

DIRECTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "directions": {
            "type": "array",
            "items": DIRECTION_SCHEMA,
            "minItems": 3,
            "maxItems": 3,
        }
    },
    "required": ["directions"],
    "additionalProperties": False,
}

REGENERATE_DIRECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"direction": DIRECTION_SCHEMA},
    "required": ["direction"],
    "additionalProperties": False,
}

SCREEN_FIELD_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"name": {"type": "string"}, "type": {"type": "string"}},
    "required": ["name", "type"],
    "additionalProperties": False,
}

APP_SPEC_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "app_name": {"type": "string"},
        "bundle_id": {"type": "string"},
        "onboarding": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                "required": ["title", "body"],
                "additionalProperties": False,
            },
        },
        "paywall_title": {"type": "string"},
        "paywall_body": {"type": "string"},
        "paywall_cta": {"type": "string"},
        "screens": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "purpose": {"type": "string"},
                    "fields": {"type": "array", "items": SCREEN_FIELD_SCHEMA},
                },
                "required": ["id", "purpose", "fields"],
                "additionalProperties": False,
            },
        },
        "data_models": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "fields": {"type": "array", "items": SCREEN_FIELD_SCHEMA},
                },
                "required": ["name", "fields"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "app_name",
        "bundle_id",
        "onboarding",
        "paywall_title",
        "paywall_body",
        "paywall_cta",
        "screens",
        "data_models",
    ],
    "additionalProperties": False,
}

FILE_OPS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": ["write", "patch", "delete"]},
                    "path": {"type": "string"},
                    "content": {"type": ["string", "null"]},
                    "find": {"type": ["string", "null"]},
                    "replace": {"type": ["string", "null"]},
                },
                "required": ["op", "path", "content", "find", "replace"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["operations"],
    "additionalProperties": False,
}


class ContrastPair(BaseModel):
    model_config = _FORBID
    name: str
    foreground: str
    background: str


class TokenColors(BaseModel):
    model_config = _FORBID
    primary: str
    on_primary: str
    surface: str
    on_surface: str


class DesignTokens(BaseModel):
    model_config = _FORBID
    colors: TokenColors
    contrast_pairs: list[ContrastPair] = Field(min_length=1)
    corner_radius: float
    typography: str


class Direction(BaseModel):
    model_config = _FORBID
    name: str
    rationale: str
    tokens: DesignTokens


class DirectionsPlan(BaseModel):
    model_config = _FORBID
    directions: list[Direction] = Field(min_length=3, max_length=3)


class OnboardingSlide(BaseModel):
    model_config = _FORBID
    title: str
    body: str


class ScreenField(BaseModel):
    model_config = _FORBID
    name: str
    type: str


class ScreenSpec(BaseModel):
    model_config = _FORBID
    id: str
    purpose: str
    fields: list[ScreenField]


class DataModel(BaseModel):
    model_config = _FORBID
    name: str
    fields: list[ScreenField]


class AppSpec(BaseModel):
    model_config = _FORBID
    app_name: str
    bundle_id: str
    onboarding: list[OnboardingSlide] = Field(min_length=3, max_length=3)
    paywall_title: str
    paywall_body: str
    paywall_cta: str
    screens: list[ScreenSpec] = Field(max_length=5)
    data_models: list[DataModel]


def schema_errors(obj: Any, model: type[BaseModel]) -> list[str]:
    try:
        model.model_validate(obj)
        return []
    except ValidationError as exc:
        return [f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in exc.errors()]
