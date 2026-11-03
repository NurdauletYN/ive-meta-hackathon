# Status — 2026-11-04 ~01:35 UTC+5

Deadline: Thu Nov 5, 07:00 UTC+5 (Wed Nov 4, 9:00 PM ET). About 29 hours left.

Track: Indie / Push the Frontier. Public standalone repo. Not the private Ive product.

## Phase

End of measurement, start of product-facing demo. Engine and studio are on `main` (PRs #1–#10). The built Flutter app still looks like the capsule shell, not the idea. The 8-idea sweep was started once and is **not** a published result.

## What is on `main`

- **Rocket:** Flutter capsule (`lib/core/` protected), file guard, 7 preflight checks that search all of `lib/`.
- **Pilot:** `complete_json` + usage.jsonl + `--max-usd`. Muse Spark, Baseten `meta-models/muse-spark-open-1026`, FakePilot.
- **`harness design` / `build`:** three directions (contrast + hue diversity); harness vs bare with 2 repair rounds.
- **Studio** (`http://127.0.0.1:8765/`): token skins in a phone, SSE events, pick a look, compare. Details drawer holds the log.
- **`harness sweep`:** first version (sequential, no infra/quality split). Do not treat its output as a result yet.
- 81 tests. `HACKATHON_RULES.md`, `PLAN.md`, `HACKATHON_SCOPE.md`.

## Honest gaps

1. **The built app is not the product.** Home is still "Rocket Capsule" / Upgrade / Settings. The generated screen is a link. Spec `app_name` never reaches Flutter. The HTML skin looks more like an app than the Flutter build.
2. **Sweep is not a fair table yet.** First bare arm timed out (`MetaRetryExhaustedError`). Timeouts must not be counted as quality failures. UI and sweep shared one API key.
3. **Slow:** a live harness build is ~100–210s.
4. **Submit blockers:** repo still private; no 3-minute video; README results table empty.

## Spend so far

About **$0.69** in `ivebench/results/usage.jsonl` (studio smokes + first sweep idea). Not a published eval.

## Next (in this cycle)

1. Branding + generated screen as home + stateful prompt + WARN if the home is static. Studio draft/step bar if small.
2. Harden `harness sweep`: matrix, infra vs quality, resume, dirty-tree refusal. **Do not run it in this cycle.**
3. `harness report` → `results.md` (counts only).
4. Offline tests for sweep failure paths. Tag `v0.3-experiment`.

## Human (not code)

- Claim Meta $150 by Nov 4, 9 PM ET. Rotate the key that was pasted in chat.
- Make the repo public before submit. Optional Baseten $100.

## Cut order

Baseten arm, then studio polish, then extra ideas. Minimum submit: public repo, 3-minute video, one honest harness-vs-bare comparison with timeouts labeled as infra.
