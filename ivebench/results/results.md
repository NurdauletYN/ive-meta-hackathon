# Sweep results

Counts only. Infra failures are listed separately and are **not** quality failures.

## Per pilot and mode

| Pilot | Mode | passed / completed | passed / attempted | median cost (pass) | median repairs (pass) | median wall s (pass) |
| --- | --- | --- | --- | --- | --- | --- |
| — | — | 0/0 | 0/0 | — | — | — |

No classified sweep JSON (`outcome` in pass / quality_fail / infra_fail) is committed in this folder.

## Infra failures (not quality)

None in this folder.

## Per idea

| Idea | Pilot | Mode | Outcome | Cost | Repairs | Wall s |
| --- | --- | --- | --- | --- | --- | --- |

## Limits

- 8 ideas in `ivebench/ideas.jsonl` (no banned topics).
- Capsule auth and billing are in-memory mocks.
- The gate and preflight checks were designed around the capsule; bare mode is scored with the same checks, searching all of `lib/`.
- Timeouts, 429s, and 5xx are `infra_fail` and are retried once. They are not quality failures.
