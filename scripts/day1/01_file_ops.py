"""Day 1 (a): does Muse Spark return valid file-operations JSON for a tiny Flutter prompt?

Runs the same prompt 10 times. For each run we check:
  - schema_valid: JSON matches FILE_OPS_SCHEMA and the local FileOp rules
  - matches: the operations are exactly the three expected (patch main.dart, write card.dart, delete old_screen.dart)
PASS if at least 9 of 10 runs match. Both rates are printed either way.

No seed is sent: the Meta docs do not document one for Muse Spark, so runs are not bit-reproducible.
Raw responses go to ivebench/results/day1/a_file_ops/.
"""

from __future__ import annotations

import statistics

from _common import RESULTS_DIR, load_client, run_guarded, save_json, verdict
from file_ops import FILE_OPS_SCHEMA, PROMPT, check_plan
from meta_client import MuseSpark

RUNS = 10
REQUIRED_MATCHES = 9


def main() -> int:
    client = load_client()
    muse = MuseSpark(client)
    out_dir = RESULTS_DIR / "a_file_ops"
    schema_valid = 0
    matches = 0
    latencies: list[float] = []

    for run in range(1, RUNS + 1):
        result = muse.generate_structured(PROMPT, schema=FILE_OPS_SCHEMA, schema_name="FileOpsPlan")
        ok_schema, ok_match, problems = check_plan(result.data)
        schema_valid += ok_schema
        matches += ok_match
        record = client.usage.records[-1]
        if record.latency_ms is not None:
            latencies.append(record.latency_ms)
        save_json(
            out_dir / f"run_{run:02d}.json",
            {
                "run": run,
                "response_id": result.response_id,
                "schema_valid": ok_schema,
                "matches_expected": ok_match,
                "problems": problems,
                "output_text": result.text,
                "usage": {
                    "input_tokens": record.input_tokens,
                    "output_tokens": record.output_tokens,
                    "reasoning_tokens": record.reasoning_tokens,
                    "est_cost_usd": record.est_cost_usd,
                    "latency_ms": record.latency_ms,
                },
            },
        )
        print(f"run {run:02d}: schema_valid={ok_schema} matches={ok_match} {'; '.join(problems)}")

    summary = {
        "runs": RUNS,
        "schema_valid": schema_valid,
        "matches_expected": matches,
        "latency_ms_median": round(statistics.median(latencies), 1) if latencies else None,
        "cost_usd_total": round(sum(r.est_cost_usd or 0 for r in client.usage.records if r.op == "text.structured"), 5),
    }
    save_json(out_dir / "summary.json", summary)
    print(f"schema valid: {schema_valid}/{RUNS}, matches expected: {matches}/{RUNS}, "
          f"median latency {summary['latency_ms_median']} ms, cost ${summary['cost_usd_total']}")
    return verdict(
        "(a) file ops JSON",
        matches >= REQUIRED_MATCHES,
        f"{matches}/{RUNS} runs matched expected operations ({schema_valid}/{RUNS} schema-valid)",
    )


if __name__ == "__main__":
    run_guarded(main)
