"""Load pilots.yaml and construct a Pilot. No live calls unless keys are present."""

from __future__ import annotations

from pathlib import Path

from .fake import FakePilot
from .muse import MuseSparkPilot
from .openai_compat import from_env as openai_from_env


def _parse_simple_yaml(text: str) -> dict[str, dict[str, str]]:
    """Minimal YAML subset: mapping of mappings with string values. No tags, no lists."""
    root: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current = line[:-1].strip()
            root[current] = {}
            continue
        if current is None or ":" not in line:
            raise ValueError(f"unsupported YAML line: {raw!r}")
        key, _, value = line.strip().partition(":")
        root[current][key.strip()] = value.strip().strip('"').strip("'")
    return root


def load_pilots_yaml(path: Path) -> dict[str, dict[str, str]]:
    return _parse_simple_yaml(path.read_text(encoding="utf-8"))


def make_pilot(name: str, config: dict[str, str] | None = None, *, fake: FakePilot | None = None):
    kind = (config or {}).get("type") or name
    if kind == "fake" or name == "fake":
        return fake if fake is not None else FakePilot()
    if kind in ("muse", "muse_spark"):
        return MuseSparkPilot()
    if kind in ("openai_compat", "baseten"):
        cfg = config or {}
        return openai_from_env(
            base_url_env=cfg.get("base_url_env", "OPENAI_COMPAT_BASE_URL"),
            api_key_env=cfg.get("api_key_env", "OPENAI_COMPAT_API_KEY"),
            model=cfg.get("model", "meta-models/muse-spark-open-1026"),
        )
    raise KeyError(f"unknown pilot {name!r} type {kind!r}")


def load_pilot(name: str, yaml_path: Path, *, fake: FakePilot | None = None):
    table = load_pilots_yaml(yaml_path) if yaml_path.is_file() else {}
    if name == "fake":
        return fake if fake is not None else FakePilot()
    if name not in table and name in ("muse", "fake"):
        return make_pilot(name, fake=fake)
    if name not in table:
        raise KeyError(f"pilot {name!r} not in {yaml_path}")
    return make_pilot(name, table[name], fake=fake)
