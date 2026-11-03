"""CLI entry: ``harness gate <project_dir> [--build-web]``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from harness.gate import gate_json, run_gate


def main() -> None:
    parser = argparse.ArgumentParser(prog="harness", description="Rocket Flutter shipping harness")
    sub = parser.add_subparsers(dest="command", required=True)

    gate = sub.add_parser("gate", help="Run analyze, optional web build, and preflight checks")
    gate.add_argument("project_dir", type=Path, help="Flutter project root (contains pubspec.yaml)")
    gate.add_argument("--build-web", action="store_true", help="Also run flutter build web --release")

    args = parser.parse_args()
    if args.command == "gate":
        report = run_gate(args.project_dir, build_web=args.build_web)
        print(gate_json(report))
        sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
