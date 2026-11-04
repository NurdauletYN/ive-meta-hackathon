"""CLI: gate, design, design pick, serve, build, ship."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pilot.config import load_pilot
from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from pilot.usage_log import DEFAULT_USAGE_PATH

from harness.build import run_build
from harness.design import pick_direction, run_design
from harness.gate import gate_json, run_gate
from harness.serve import serve
from harness.report import write_results, write_results_html
from harness.ship import ShipError, run_ship
from harness.sweep import DirtyTreeError, load_ideas, run_sweep
from harness.ui import serve_ui
from harness.usage_report import load_usage, patch_metause, render_usage

ROOT = Path(__file__).resolve().parents[2]


def _session(pilot_name: str, run_id: str, max_usd: float | None, fake=None) -> PilotSession:
    yaml_path = ROOT / "pilots.yaml"
    pilot = load_pilot(pilot_name, yaml_path, fake=fake)
    return PilotSession(pilot, run_id=run_id, usage_path=ROOT / DEFAULT_USAGE_PATH, max_usd=max_usd)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="harness", description="Rocket Flutter shipping harness")
    sub = parser.add_subparsers(dest="command", required=True)

    gate = sub.add_parser("gate", help="Run analyze, optional web build, and preflight checks")
    gate.add_argument("project_dir", type=Path)
    gate.add_argument("--build-web", action="store_true")

    design = sub.add_parser("design", help="Propose 3 design directions or pick one")
    design.add_argument("idea_or_pick")
    design.add_argument("rest", nargs="*")
    design.add_argument("--pilot", default="muse")
    design.add_argument("--out", type=Path)
    design.add_argument("--max-usd", type=float, default=None)
    design.add_argument("--skip-web", action="store_true", help="Copy capsule and apply tokens without flutter build web")

    build = sub.add_parser("build", help="Spec + file ops + gate/repair")
    build.add_argument("idea")
    build.add_argument("--pilot", default="muse")
    build.add_argument("--mode", choices=("harness", "bare"), required=True)
    build.add_argument("--run", required=True, help="run id, also used as runs/<id>")
    build.add_argument("--max-usd", type=float, default=None)

    srv = sub.add_parser("serve", help="Serve a design-run directory")
    srv.add_argument("run_dir", type=Path)
    srv.add_argument("--port", type=int, default=8765)

    ui = sub.add_parser("ui", help="Local dashboard to run design/build/gate")
    ui.add_argument("--port", type=int, default=8765)

    sweep = sub.add_parser("sweep", help="Each idea × live pilots × harness/bare into ivebench/results")
    sweep.add_argument("--pilots", default="muse,baseten", help="comma-separated --pilot names")
    sweep.add_argument("--max-usd", type=float, default=8)
    sweep.add_argument("--max-usd-per-pilot", type=float, default=4)
    sweep.add_argument("--limit", type=int, default=None)
    sweep.add_argument("--build-web", action="store_true")
    sweep.add_argument("--call-timeout", type=float, default=300)
    sweep.add_argument("--run-timeout", type=float, default=900)

    report = sub.add_parser("report", help="Write counts-only results.md from a sweep folder")
    report.add_argument("--in", dest="indir", type=Path, default=ROOT / "ivebench" / "results" / "sweep")
    report.add_argument("--out", dest="outfile", type=Path, default=ROOT / "ivebench" / "results" / "results.md")
    report.add_argument("--html", nargs="?", const="DEFAULT", default=None, help="Also write a static HTML page (GitHub Pages)")

    ship = sub.add_parser("ship", help="Build an IPA and upload to App Store Connect / TestFlight")
    ship.add_argument("project_dir", type=Path)
    ship.add_argument("--target", choices=("testflight",), default="testflight")
    ship.add_argument("--dry-run", action="store_true", help="Validate inputs and print commands; execute nothing")

    usage = sub.add_parser("usage-report", help="Aggregate usage.jsonl by model and stage")
    usage.add_argument("--in", dest="usage_path", type=Path, default=ROOT / "ivebench" / "results" / "usage.jsonl")
    usage.add_argument("--write-metause", action="store_true", help="Replace the marked table in METAUSE.md")
    usage.add_argument("--out", dest="usage_out", type=Path, default=None)

    args = parser.parse_args(argv)
    try:
        _dispatch(args)
    except BudgetExceeded as exc:
        print(json.dumps({"ok": False, "error": "budget_exceeded", "message": str(exc)}), file=sys.stderr)
        sys.exit(3)
    except DirtyTreeError as exc:
        print(json.dumps({"ok": False, "error": "dirty_tree", "message": str(exc)}), file=sys.stderr)
        sys.exit(2)
    except ShipError as exc:
        print(json.dumps({"ok": False, "error": "ship", "message": str(exc)}), file=sys.stderr)
        sys.exit(1)


def _dispatch(args: argparse.Namespace) -> None:
    if args.command == "gate":
        report = run_gate(args.project_dir, build_web=args.build_web)
        print(gate_json(report))
        sys.exit(0 if report.ok else 1)

    if args.command == "serve":
        serve(args.run_dir.resolve(), port=args.port)
        return

    if args.command == "ui":
        serve_ui(ROOT, port=args.port)
        return

    if args.command == "design":
        if args.idea_or_pick == "pick":
            if len(args.rest) < 2:
                raise SystemExit("usage: harness design pick <run_id> <n>")
            run_id, n_s = args.rest[0], args.rest[1]
            path = pick_direction(ROOT / "runs" / run_id, int(n_s))
            print(path.read_text(encoding="utf-8"))
            return
        idea = args.idea_or_pick
        out = args.out or ROOT / "runs" / "design"
        run_id = out.name
        session = _session(args.pilot, run_id, args.max_usd)
        skip = (lambda _p: (True, "skipped")) if args.skip_web else None
        result = run_design(
            idea, session, capsule=ROOT / "flutter_template", out_dir=out, build_fn=skip
        )
        print(json.dumps({k: v for k, v in result.items() if k != "directions"}, indent=2, default=str))
        print(json.dumps({"directions": [d["name"] for d in result["directions"]]}, indent=2))
        return

    if args.command == "build":
        session = _session(args.pilot, args.run, args.max_usd)
        result = run_build(
            args.idea,
            session,
            mode=args.mode,
            run_dir=ROOT / "runs" / args.run,
            capsule=ROOT / "flutter_template",
        )
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result["ok"] else 1)

    if args.command == "sweep":
        ideas = load_ideas(ROOT / "ivebench" / "ideas.jsonl")
        if args.limit:
            ideas = ideas[: args.limit]
        names = [p.strip() for p in args.pilots.split(",") if p.strip()]

        def make_session(run_id: str, pilot_name: str, max_usd: float | None) -> PilotSession:
            return _session(pilot_name, run_id, max_usd)

        summary = run_sweep(
            ideas=ideas,
            make_session=make_session,
            capsule=ROOT / "flutter_template",
            out_dir=ROOT / "ivebench" / "results" / "sweep",
            runs=ROOT / "runs",
            usage_path=ROOT / DEFAULT_USAGE_PATH,
            pilots=names,
            max_usd=args.max_usd,
            max_usd_per_pilot=args.max_usd_per_pilot,
            build_web=args.build_web,
            git_repo=ROOT,
            require_clean_git=True,
            call_timeout_s=args.call_timeout,
            run_timeout_s=args.run_timeout,
            log_path=ROOT / "runs" / "sweep.log",
        )
        print(json.dumps(summary, indent=2, default=str))
        failed = any(r.get("outcome") == "quality_fail" for r in summary["rows"])
        sys.exit(1 if failed else 0)

    if args.command == "report":
        path = write_results(args.indir, args.outfile)
        print(path.read_text(encoding="utf-8"))
        if args.html is not None:
            html_path = (
                ROOT / "ivebench" / "results" / "index.html"
                if args.html == "DEFAULT"
                else Path(args.html)
            )
            wrote = write_results_html(args.indir, html_path)
            print(f"wrote {wrote}")
        return

    if args.command == "usage-report":
        table = render_usage(load_usage(args.usage_path))
        print(table)
        if args.write_metause:
            path = patch_metause(ROOT / "METAUSE.md", table)
            print(f"wrote {path}")
        if args.usage_out:
            args.usage_out.write_text(table, encoding="utf-8")
        return

    if args.command == "ship":
        result = run_ship(args.project_dir, target=args.target, dry_run=args.dry_run)
        if result.get("dry_run"):
            print("DRY-RUN (nothing executed)")
            for cmd in result.get("commands") or result.get("planned") or []:
                print(cmd)
        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
