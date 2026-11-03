"""Self-contained HTML phone screen from design tokens. Not a Flutter build."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path
from typing import Any

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _color(value: str | None, fallback: str) -> str:
    text = (value or "").strip()
    return text if _HEX.match(text) else fallback


def _radius(value: Any, fallback: float = 14.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(4.0, min(number, 36.0))


def write_skin(
    path: Path,
    *,
    title: str,
    app_name: str,
    idea: str = "",
    primary: str = "#1565C0",
    on_primary: str = "#FFFFFF",
    surface: str = "#F5F7FA",
    on_surface: str = "#1A1A1A",
    radius: float = 14.0,
    typography: str = "default",
    items: list[str] | None = None,
    cta: str = "Open",
) -> Path:
    """Write a 390×844 CSS screen that iframes like a Flutter web preview."""
    primary = _color(primary, "#1565C0")
    on_primary = _color(on_primary, "#FFFFFF")
    surface = _color(surface, "#F5F7FA")
    on_surface = _color(on_surface, "#1A1A1A")
    radius = _radius(radius)
    size = {"compact": "14px", "expressive": "18px"}.get(typography, "16px")
    weight = "600" if typography == "expressive" else "500"
    rows = [escape(item) for item in (items or ["Today", "Saved", "Activity"])[:4]]
    if not rows:
        rows = ["Today", "Saved", "Activity"]
    lis = "".join(f"<li><span>{row}</span><em>Open</em></li>" for row in rows)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(app_name)}</title>
  <style>
    html, body {{ margin: 0; height: 100%; background: {surface}; color: {on_surface};
      font: {size}/1.4 system-ui, sans-serif; }}
    body {{ display: flex; flex-direction: column; min-height: 100%; }}
    header {{ padding: 48px 20px 16px; }}
    header p {{ margin: 0; opacity: 0.55; font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; }}
    h1 {{ margin: 6px 0 0; font-size: 28px; font-weight: {weight}; letter-spacing: -0.03em; }}
    .idea {{ margin: 8px 0 0; opacity: 0.72; }}
    ul {{ list-style: none; margin: 8px 16px; padding: 0; flex: 1; }}
    li {{ display: flex; justify-content: space-between; align-items: center;
      background: {surface}; border: 1px solid {primary};
      border-radius: {radius}px; padding: 14px 16px; margin: 10px 0; }}
    li em {{ font-style: normal; color: {primary}; font-size: 13px; }}
    footer {{ padding: 16px 20px 28px; }}
    button {{ width: 100%; border: 0; background: {primary}; color: {on_primary};
      border-radius: {radius}px; padding: 14px; font: inherit; font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <p>{escape(title)}</p>
    <h1>{escape(app_name)}</h1>
    <p class="idea">{escape((idea or "")[:140])}</p>
  </header>
  <ul>{lis}</ul>
  <footer><button type="button">{escape(cta)}</button></footer>
</body>
</html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def write_skin_from_project(
    project: Path,
    *,
    title: str,
    app_name: str,
    idea: str = "",
    items: list[str] | None = None,
    cta: str = "Open",
) -> Path:
    tokens_path = project / "lib" / "app" / "design_tokens.json"
    colors = {"primary": "#1565C0", "on_primary": "#FFFFFF", "surface": "#F5F7FA", "on_surface": "#1A1A1A"}
    radius = 14.0
    typography = "default"
    if tokens_path.is_file():
        try:
            data = json.loads(tokens_path.read_text(encoding="utf-8"))
            colors.update(data.get("colors") or {})
            radius = data.get("corner_radius", radius)
            typography = str(data.get("typography") or typography)
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return write_skin(
        project / "skin.html",
        title=title,
        app_name=app_name,
        idea=idea,
        primary=str(colors.get("primary") or ""),
        on_primary=str(colors.get("on_primary") or ""),
        surface=str(colors.get("surface") or ""),
        on_surface=str(colors.get("on_surface") or ""),
        radius=radius,
        typography=typography,
        items=items,
        cta=cta,
    )
