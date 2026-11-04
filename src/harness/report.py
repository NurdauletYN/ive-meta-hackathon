"""Counts-only sweep report. No significance claims."""

from __future__ import annotations

import html
import json
from pathlib import Path
from statistics import median
from typing import Any


VALID_OUTCOMES = {"pass", "quality_fail", "infra_fail", "skipped"}


def load_runs(out_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not out_dir.is_dir():
        return rows
    for path in sorted(out_dir.glob("sweep-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        if str(data.get("outcome") or "") not in VALID_OUTCOMES:
            continue
        rows.append(data)
    return rows


def _cost(row: dict[str, Any]) -> float:
    tokens = row.get("tokens") or {}
    if isinstance(tokens, dict):
        return float(tokens.get("est_cost_usd") or 0.0)
    return 0.0


def _median(values: list[float]) -> str:
    if not values:
        return "—"
    return f"{median(values):.4g}"


def render_results(rows: list[dict[str, Any]]) -> str:
    pilots = sorted({str(r.get("pilot") or "unknown") for r in rows})
    modes = ("harness", "bare")
    lines = [
        "# Sweep results",
        "",
        "Counts only. Infra failures are listed separately and are **not** quality failures.",
        "",
        "## Per pilot and mode",
        "",
        "| Pilot | Mode | passed / completed | passed / attempted | median cost (pass) | median repairs (pass) | median wall s (pass) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not rows:
        lines.append("| — | — | 0/0 | 0/0 | — | — | — |")
        lines.append("")
        lines.append("No classified sweep JSON (`outcome` in pass / quality_fail / infra_fail) is committed in this folder.")
    for pilot in pilots:
        for mode in modes:
            group = [r for r in rows if r.get("pilot") == pilot and r.get("mode") == mode]
            if not group:
                continue
            passed = [r for r in group if r.get("outcome") == "pass"]
            quality = [r for r in group if r.get("outcome") == "quality_fail"]
            infra = [r for r in group if r.get("outcome") == "infra_fail"]
            skipped = [r for r in group if r.get("outcome") == "skipped" or r.get("skipped")]
            completed = len(passed) + len(quality)
            attempted = completed + len(infra)
            pc = f"{len(passed)}/{completed}" if completed else "0/0"
            pa = f"{len(passed)}/{attempted}" if attempted else "0/0"
            costs = [_cost(r) for r in passed]
            repairs = [float(r.get("repair_rounds") or 0) for r in passed]
            walls = [float(r.get("wall_ms") or 0) / 1000.0 for r in passed]
            lines.append(
                f"| {pilot} | {mode} | {pc} | {pa} | ${_median(costs) if costs else '—'} | "
                f"{_median(repairs)} | {_median(walls)} |"
            )
            _ = skipped
    lines += ["", "## Infra failures (not quality)", ""]
    infras = [r for r in rows if r.get("outcome") == "infra_fail"]
    if not infras:
        lines.append("None in this folder.")
    else:
        lines.append("| Run | Pilot | Mode | Error |")
        lines.append("| --- | --- | --- | --- |")
        for row in infras:
            err = str(row.get("error") or "")[:160].replace("|", "/")
            lines.append(
                f"| {row.get('run_id')} | {row.get('pilot')} | {row.get('mode')} | {err} |"
            )
    lines += ["", "## Per idea", ""]
    lines.append("| Idea | Pilot | Mode | Outcome | Cost | Repairs | Wall s |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for row in sorted(rows, key=lambda r: (str(r.get("idea") or ""), str(r.get("pilot") or ""), str(r.get("mode") or ""))):
        if row.get("outcome") == "skipped" and row.get("resumed"):
            continue
        lines.append(
            f"| {row.get('idea') or row.get('run_id')} | {row.get('pilot')} | {row.get('mode')} | "
            f"{row.get('outcome')} | ${_cost(row):.4f} | {row.get('repair_rounds') or 0} | "
            f"{float(row.get('wall_ms') or 0)/1000:.1f} |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "- 8 ideas in `ivebench/ideas.jsonl` (no banned topics).",
        "- Capsule auth and billing are in-memory mocks.",
        "- The gate and preflight checks were designed around the capsule; bare mode is scored with the same checks, searching all of `lib/`.",
        "- Timeouts, 429s, and 5xx are `infra_fail` and are retried once. They are not quality failures.",
        "",
    ]
    return "\n".join(lines)


def write_results(out_dir: Path, dest: Path) -> Path:
    text = render_results(load_runs(out_dir))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


def _td(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def render_results_html(rows: list[dict[str, Any]]) -> str:
    md = render_results(rows)
    current: list[str] = []
    body_chunks: list[str] = []
    for line in md.splitlines():
        if line.startswith("#"):
            if current:
                body_chunks.append(_md_table_to_html(current))
                current = []
            level = 2 if line.startswith("##") else 1
            text = line.lstrip("#").strip()
            tag = "h1" if level == 1 else "h2"
            body_chunks.append(f"<{tag}>{_td(text)}</{tag}>")
        elif line.startswith("|"):
            current.append(line)
        else:
            if current:
                body_chunks.append(_md_table_to_html(current))
                current = []
            if line.strip():
                body_chunks.append(f"<p>{_td(line)}</p>")
    if current:
        body_chunks.append(_md_table_to_html(current))
    inner = "\n".join(body_chunks)
    return (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\"/>"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>"
        "<title>Rocket sweep results</title>"
        "<style>"
        "body{font-family:system-ui,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;color:#1a1a1a;background:#faf8f5}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:0.92rem}"
        "th,td{border:1px solid #ddd;padding:0.4rem 0.55rem;text-align:left}"
        "th{background:#efeae3}"
        "h1,h2{letter-spacing:-0.03em}"
        "p{color:#444}"
        "</style></head><body>\n"
        f"{inner}\n"
        "<p>Static page. No API keys. No live calls. Generated by <code>harness report --html</code>.</p>"
        "</body></html>\n"
    )


def _md_table_to_html(lines: list[str]) -> str:
    rows = []
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if i == 1 and all(set(c) <= set("-: ") for c in cells):
            continue
        tag = "th" if i == 0 else "td"
        rows.append("<tr>" + "".join(f"<{tag}>{_td(c)}</{tag}>" for c in cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def write_results_html(out_dir: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_results_html(load_runs(out_dir)), encoding="utf-8")
    return dest
