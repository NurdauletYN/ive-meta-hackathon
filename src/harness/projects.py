"""Projects for the studio: every build or improve is a version; versions share a project id.

Layout: runs/<run_id>/meta.json. A project is the set of metas with the same `project`.
"""

from __future__ import annotations

import fnmatch
import io
import json
import re
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .palettes import PALETTES

META_NAME = "meta.json"

_SKIP_DIRS = {"build", ".dart_tool", ".git", ".idea", "Pods", ".gradle", "DerivedData", "node_modules", ".symlinks"}
# Never ship secrets or build output in a code download.
_SKIP_FILES = (
    "skin.html",
    "ship_report.json",
    ".env",
    ".env.*",
    "*.env",
    "GoogleService-Info.plist",
    "google-services.json",
    "*.p8",
    "*.p12",
    "*.pem",
    "*.key",
    "*.jks",
    "*.keystore",
    "key.properties",
    ".flutter-plugins-dependencies",
    ".DS_Store",
)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def read_meta(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / META_NAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def palette_for_project(project: Path) -> dict[str, str] | None:
    tokens = project / "lib" / "app" / "design_tokens.json"
    try:
        primary = str(json.loads(tokens.read_text(encoding="utf-8"))["colors"]["primary"]).upper()
    except (OSError, KeyError, json.JSONDecodeError, TypeError):
        return None
    for palette in PALETTES:
        if palette.primary.upper() == primary:
            return {"id": palette.id, "name": palette.name, "primary": palette.primary, "dark": palette.dark}
    return {"id": "custom", "name": "Custom", "primary": primary, "dark": False}


def _app_name(run_dir: Path) -> str | None:
    try:
        spec = json.loads((run_dir / "spec.json").read_text(encoding="utf-8"))
        name = spec.get("app_name")
        return str(name) if name else None
    except (OSError, json.JSONDecodeError):
        return None


def _next_version(runs: Path, project_id: str) -> int:
    top = 0
    if runs.is_dir():
        for child in runs.iterdir():
            meta = read_meta(child) if child.is_dir() else None
            if meta and meta.get("project") == project_id:
                top = max(top, int(meta.get("version") or 0))
    return top + 1


def write_meta(
    runs: Path,
    run_id: str,
    *,
    kind: str,
    instruction: str,
    pilot: str,
    ok: bool,
    from_run: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    run_dir = runs / run_id
    parent = read_meta(runs / from_run) if from_run else None
    project_id = str(parent["project"]) if parent and parent.get("project") else (from_run or run_id)
    title = (parent or {}).get("title") or " ".join(instruction.split())[:60]
    meta = {
        "run_id": run_id,
        "project": project_id,
        "version": max(2, _next_version(runs, project_id)) if from_run else 1,
        "parent": from_run,
        "kind": kind,
        "title": title,
        "app_name": _app_name(run_dir) or (parent or {}).get("app_name"),
        "instruction": " ".join(instruction.split())[:400],
        "pilot": pilot,
        "ok": ok,
        "error": error,
        "palette": palette_for_project(run_dir / "project"),
        "created": _now(),
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / META_NAME).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def _preview_url(runs: Path, run_id: str) -> str | None:
    web = runs / run_id / "project" / "build" / "web" / "index.html"
    if web.is_file():
        return f"/runs/{run_id}/project/build/web/"
    skin = runs / run_id / "project" / "skin.html"
    return f"/runs/{run_id}/project/skin.html" if skin.is_file() else None


def _metas(runs: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not runs.is_dir():
        return out
    for child in runs.iterdir():
        if child.is_dir():
            meta = read_meta(child)
            if meta and meta.get("project"):
                out.append(meta)
    return out


def list_projects(runs: Path) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for meta in _metas(runs):
        grouped.setdefault(str(meta["project"]), []).append(meta)
    projects = []
    for project_id, versions in grouped.items():
        versions.sort(key=lambda m: (int(m.get("version") or 0), str(m.get("created"))))
        first, last = versions[0], versions[-1]
        projects.append(
            {
                "id": project_id,
                "title": last.get("app_name") or first.get("title") or project_id,
                "subtitle": first.get("title"),
                "versions": len(versions),
                "latest_run": last["run_id"],
                "ok": bool(last.get("ok")),
                "palette": last.get("palette"),
                "updated": last.get("created"),
            }
        )
    projects.sort(key=lambda p: str(p.get("updated")), reverse=True)
    return projects


def get_project(runs: Path, project_id: str) -> dict[str, Any] | None:
    versions = [m for m in _metas(runs) if m.get("project") == project_id]
    if not versions:
        return None
    versions.sort(key=lambda m: (int(m.get("version") or 0), str(m.get("created"))))
    items = []
    for meta in versions:
        items.append(
            {
                "run_id": meta["run_id"],
                "version": meta.get("version"),
                "parent": meta.get("parent"),
                "instruction": meta.get("instruction"),
                "ok": bool(meta.get("ok")),
                "error": meta.get("error"),
                "palette": meta.get("palette"),
                "created": meta.get("created"),
                "preview": _preview_url(runs, str(meta["run_id"])),
            }
        )
    last = versions[-1]
    return {
        "id": project_id,
        "title": last.get("app_name") or versions[0].get("title"),
        "versions": items,
        "latest_run": last["run_id"],
    }


def _skipped(rel: Path) -> bool:
    if any(part in _SKIP_DIRS for part in rel.parts[:-1]):
        return True
    return any(fnmatch.fnmatch(rel.name, pattern) for pattern in _SKIP_FILES)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "app"


README = """# {name}

Flutter app generated by Rocket (version {version}).

```
flutter pub get
flutter run -d chrome
```

`lib/app/features/` holds the generated screens. `lib/core/` is the locked shell (auth, billing,
router, design kit). Auth and billing run in demo mode until you add your own Firebase and
RevenueCat config; no keys are included in this download.
"""


def build_zip(runs: Path, run_id: str) -> tuple[str, bytes] | None:
    """(download name, zip bytes) for a run's project, or None if there is no project."""
    run_dir = runs / run_id
    project = run_dir / "project"
    if not project.is_dir() or not (project / "pubspec.yaml").is_file():
        return None
    meta = read_meta(run_dir) or {}
    name = str(meta.get("app_name") or meta.get("title") or run_id)
    slug = _slug(name)
    version = meta.get("version") or 1
    buffer = io.BytesIO()
    root = f"{slug}-v{version}"
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(project.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(project)
            if _skipped(rel):
                continue
            archive.write(path, f"{root}/{rel.as_posix()}")
        archive.writestr(f"{root}/README.md", README.format(name=name, version=version))
    return f"{root}.zip", buffer.getvalue()
