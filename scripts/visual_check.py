"""Offline visual check: build the canned app for an idea (palette picked from the idea) and open it.

    uv run python scripts/visual_check.py "sportswear shop" vis-sport

Writes runs/<run-id>/ with a web build. No API calls.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harness.build import run_build  # noqa: E402
from harness.palettes import pick_palette  # noqa: E402
from pilot.canned import canned_pilot  # noqa: E402
from pilot.session import PilotSession  # noqa: E402


def main() -> int:
    idea = sys.argv[1] if len(sys.argv) > 1 else "sportswear shop"
    run_id = sys.argv[2] if len(sys.argv) > 2 else "vis-check"
    session = PilotSession(canned_pilot(), run_id=run_id, usage_path=ROOT / "runs" / f"{run_id}.usage.jsonl")
    result = run_build(
        idea,
        session,
        mode="harness",
        run_dir=ROOT / "runs" / run_id,
        capsule=ROOT / "flutter_template",
        build_web=True,
        web_base_href="/",
    )
    print("palette:", pick_palette(idea).name, "| ok:", result.get("ok"), "| web:", ROOT / "runs" / run_id / "project" / "build" / "web")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
