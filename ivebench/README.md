# ivebench

| Path | Status |
| --- | --- |
| `ideas.jsonl` | 8 app ideas for Pilot design/build (no medical / mental health / nutrition / sports / job screening / political content) |
| `results/usage.jsonl` | Append-only usage log (`run_id`, pilot, stage, tokens, cached_tokens, est. cost) |
| `results/day1/` | Historical Day 1 API smokes |

Full eval sweep (every idea × harness/bare) is not in this phase. Offline FakePilot coverage is `tests/test_pilot.py`.
