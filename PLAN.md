# Plan to submission

**Deadline:** Wed Nov 4, 9:00 PM ET (= Thu Nov 5, 07:00 UTC+5). Target submit **Nov 4 ~20:30 UTC+5**.

Track recommendation: **Indie Developer**. Problem statement: **Push the Frontier**. Never use the private Ive front end.

## Phase 0 — human (credits, repo)

- [ ] Claim Meta $150 credits (form; card required). Deadline Nov 4 9 PM ET.
- [ ] Request Baseten $100; use model id `meta-models/muse-spark-open-1026`.
- [ ] Rotate the API key that was pasted in chat.
- [ ] Make this GitHub repo **public** before submit; verify logged-out.

## Phase 1 — fair measurement (this branch)

- [x] `HACKATHON_RULES.md` + always-on Cursor rule.
- [x] Preflight searches all of `lib/**` (not only capsule `lib/core/...` paths).
- [x] Price `meta-models/muse-spark-open-1026` so `--max-usd` works on Baseten.
- [x] Shorter Meta timeouts (default 90s, 2 retries) so a stall cannot burn ~16 min.
- [x] Tests for relocated layouts, open-model pricing, timeout env.

## Phase 2 — live `design` + tester UI

- [x] Local `harness ui` studio: phone-first, token skins, SSE, design pick, harness vs bare.
- [x] `harness design` one idea with Muse Spark (`Porch Light` / `Community Shed` / `Good Neighbor`).
- [ ] Playwright only if install is quick; otherwise skip.

## Phase 3 — sweep

- [ ] 8 ideas × muse,baseten × harness/bare (`uv run harness sweep --max-usd 8`). Do not run until tagged.
- [ ] Same on Baseten Muse Spark Open if keys exist. Cut Baseten at 15:00 if unfinished.
- [ ] Commit raw `ivebench/results/` and a results table.

## Phase 4–6 — demo + submit

- [ ] 3-minute video (problem, Rocket/Pilot, live design, live build + guard reject, results, limits).
- [ ] README: NEW vs PRE-EXISTING, 5-minute reproduce, results, mocks called out.
- [ ] Tag `v1.2-submission`. Submit via CV. Verify repo + video logged-out.

## Cut lines

| Behind at | Cut |
| --- | --- |
| 15:00 | Baseten arm, then voice, then icon |
| 16:30 | Prefix expansion, then screenshots |
| 19:00 | Everything except video, public repo, one fair comparison |

Minimum viable: public repo, 3-minute video, one honest harness-vs-bare comparison.
