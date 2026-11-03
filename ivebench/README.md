# ivebench

| Path | Status |
| --- | --- |
| `ideas.jsonl` | 8 app ideas for Pilot design/build (no medical / mental health / nutrition / sports / job screening / political content) |
| `results/usage.jsonl` | Append-only usage log (`run_id`, pilot, stage, tokens, cached_tokens, est. cost) |
| `results/day1/` | Historical Day 1 API smokes |

```bash
uv run harness sweep --pilots muse,baseten --max-usd 8 --max-usd-per-pilot 4
# writes ivebench/results/sweep/*.json and runs/sweep.log
# refuses a dirty git tree; skips completed run ids; retries infra_fail once
uv run harness report   # ivebench/results/results.md — counts only, infra listed separately
```

Offline FakePilot coverage is `tests/test_pilot.py` and `tests/test_sweep.py`.
