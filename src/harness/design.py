"""Propose 3 design directions, validate, copy capsule, apply tokens, optional web build."""

from __future__ import annotations

import json
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from pilot.schemas import DIRECTIONS_SCHEMA, REGENERATE_DIRECTION_SCHEMA, Direction, DirectionsPlan, schema_errors
from pilot.session import PilotSession

from .copy_project import copy_tree
from .diversity import contrast_errors, diversity_errors
from .tokens import apply_tokens
from .web_build import flutter_web_build

DESIGN_SYSTEM = """Return exactly 3 design directions. Each has name, rationale, and tokens:
colors.primary/on_primary/surface/on_surface as #RRGGBB, contrast_pairs that meet WCAG AA 4.5:1,
corner_radius (number), typography one of default|compact|expressive.
Primary hues of the three directions must differ by at least 40 degrees. At least two distinct
corner_radius or typography values across the set.
"""

BuildFn = Callable[[Path], tuple[bool, str]]


def _flutter_web_build(project: Path, base_href: str | None = None) -> tuple[bool, str]:
    return flutter_web_build(project, base_href=base_href)


def request_directions(session: PilotSession, idea: str) -> list[Direction]:
    payload = session.complete_json(DESIGN_SYSTEM, f"App idea:\n{idea}", DIRECTIONS_SCHEMA, "design")
    errors = schema_errors(payload, DirectionsPlan)
    attempts = 0
    while errors and attempts < 2:
        attempts += 1
        payload = session.complete_json(
            DESIGN_SYSTEM,
            f"Previous JSON failed validation:\n" + "\n".join(errors) + f"\n\nApp idea:\n{idea}",
            DIRECTIONS_SCHEMA,
            "design",
        )
        errors = schema_errors(payload, DirectionsPlan)
    if errors:
        raise ValueError("design JSON invalid after retries: " + "; ".join(errors))
    plan = DirectionsPlan.model_validate(payload)
    return list(plan.directions)


def _fix_diversity(session: PilotSession, idea: str, directions: list[Direction]) -> list[Direction]:
    issues = diversity_errors(directions)
    if not issues:
        return directions
    # Ask once to regenerate only the last offending direction (index 2 is the usual collision).
    index = 2 if len(directions) > 2 else 0
    user = (
        f"App idea:\n{idea}\n\nThe set of directions failed diversity:\n"
        + "\n".join(issues)
        + f"\n\nRegenerate ONLY direction index {index} ({directions[index].name}). "
        "Keep the other two unchanged in spirit. Return a single replacement direction."
    )
    payload = session.complete_json(DESIGN_SYSTEM, user, REGENERATE_DIRECTION_SCHEMA, "design_regenerate")
    replacement = payload.get("direction")
    if isinstance(replacement, dict):
        try:
            directions[index] = Direction.model_validate(replacement)
        except Exception:
            pass
    return directions


def write_gallery(run_dir: Path, directions: list[Direction]) -> Path:
    cards = []
    for index, direction in enumerate(directions, start=1):
        href = f"dir_{index}/build/web/index.html"
        cards.append(
            f'<section><h2>{index}. {direction.name}</h2>'
            f"<p>{direction.rationale}</p>"
            f'<p>primary {direction.tokens.colors.primary} · radius {direction.tokens.corner_radius} · {direction.tokens.typography}</p>'
            f'<p><a href="{href}">preview</a></p></section>'
        )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Design gallery</title>"
        "<style>body{font-family:sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem}"
        "section{border:1px solid #ccc;padding:1rem;margin:1rem 0}</style></head><body>"
        "<h1>Design directions</h1>"
        + "".join(cards)
        + "</body></html>"
    )
    path = run_dir / "gallery.html"
    path.write_text(html, encoding="utf-8")
    return path


def run_design(
    idea: str,
    session: PilotSession,
    *,
    capsule: Path,
    out_dir: Path,
    build_fn: BuildFn | None = None,
    public_prefix: str | None = None,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = public_prefix or f"/runs/{out_dir.name}/"
    session.emit("stage", name="design", status="start")
    directions = request_directions(session, idea)
    contrast_issues = [err for d in directions for err in contrast_errors(d)]
    if contrast_issues:
        directions = request_directions(session, idea + "\n\nContrast failures:\n" + "\n".join(contrast_issues))
        contrast_issues = [err for d in directions for err in contrast_errors(d)]
    directions = _fix_diversity(session, idea, directions)
    diversity_issues = diversity_errors(directions)
    contrast_issues = [err for d in directions for err in contrast_errors(d)]
    session.emit(
        "stage",
        name="design",
        status="ok",
        names=[d.name for d in directions],
        contrast_ok=not contrast_issues,
        diversity_ok=not diversity_issues,
    )

    def _one(index: int, direction: Direction) -> dict:
        dest = out_dir / f"dir_{index}"
        copy_tree(capsule, dest)
        apply_tokens(dest, direction)
        href = f"{prefix}dir_{index}/build/web/"
        skipped = build_fn is not None
        if skipped:
            ok, log = build_fn(dest)
        else:
            ok, log = _flutter_web_build(dest, href)
        preview = None if skipped or not ok else href
        session.emit(
            "direction",
            index=index,
            name=direction.name,
            primary=direction.tokens.colors.primary,
            preview=preview,
            ok=ok,
        )
        return {"dir": dest.name, "ok": ok, "log_tail": log[-500:], "preview": preview, "index": index}

    builds: list[dict] = [{}] * len(directions)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(_one, i, d): i for i, d in enumerate(directions, start=1)}
        for fut in as_completed(futs):
            item = fut.result()
            builds[item["index"] - 1] = item
    write_gallery(out_dir, directions)
    (out_dir / "directions.json").write_text(
        json.dumps({"idea": idea, "directions": [d.model_dump() for d in directions]}, indent=2),
        encoding="utf-8",
    )
    session.emit("done", ok=not contrast_issues and not diversity_issues, kind="design")
    return {
        "out_dir": str(out_dir),
        "directions": [d.model_dump() for d in directions],
        "contrast_ok": not contrast_issues,
        "diversity_ok": not diversity_issues,
        "contrast_issues": contrast_issues,
        "diversity_issues": diversity_issues,
        "builds": builds,
    }


def pick_direction(run_dir: Path, n: int) -> Path:
    data = json.loads((run_dir / "directions.json").read_text(encoding="utf-8"))
    directions = data["directions"]
    if not 1 <= n <= len(directions):
        raise ValueError(f"n must be 1..{len(directions)}")
    path = run_dir / "choice.json"
    path.write_text(json.dumps({"n": n, "direction": directions[n - 1]}, indent=2) + "\n", encoding="utf-8")
    return path
