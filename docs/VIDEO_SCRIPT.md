# 3-minute demo script

Before this week there was no public Rocket repo: no capsule, no Pilot layer, no studio, no gate. Everything in this repository was written during the Meta Global AI Developer Hackathon (Oct 27 – Nov 4 2026). The private Ive product is not in this video.

Placeholders `{RESULT_*}` are filled from `harness report` / `harness usage-report`. Do not invent numbers.

## 0:00–0:20 — What it is
Rocket is a model-agnostic harness. The harness is the rocket. The model is the pilot. You describe an app, pick a look, and the harness builds inside a locked Flutter capsule, then verifies with a deterministic gate.

## 0:20–0:50 — Studio
Open `http://127.0.0.1:8765/`. Default live pilot is Muse Spark; FakePilot is the offline demo. Type an idea. Three design directions appear as phones. Pick one. Build. The Flutter web preview loads in the frame.

Say on camera: capsule auth and billing are in-memory mocks unless the user supplies config. That is labeled demo mode.

## 0:50–1:20 — What the harness constrains
Show `lib/core/` as protected and `lib/app/` as editable. The Pilot emits JSON file ops; the guard rejects writes to core. Gate: analyze, tests, web build, preflight. Repair is at most two rounds, fed only by gate failures.

## 1:20–1:50 — Evidence, not slogans
Show the evidence panel / `ivebench/results/results.md`.
- Shippable-app rate with harness: {RESULT_HARNESS_PASS}
- Shippable-app rate without harness: {RESULT_BARE_PASS}
- Median repair rounds (pass): {RESULT_REPAIR_MEDIAN}
- Infra failures (not quality): {RESULT_INFRA}
- Cost logged: {RESULT_USAGE_COST}

State the limits on screen: small idea set, mock auth/billing, preflight pass rates are not Apple rejection rates.

## 1:50–2:20 — Ship path (unverified live unless we show a device)
`harness ship --dry-run`. Credentials never go to a model. If a TestFlight install exists, show the phone: {RESULT_TESTFLIGHT_EVIDENCE}. If not, say unverified — do not imply a store listing.

## 2:20–2:50 — Meta models
Muse Spark proposes looks and file ops. Muse Image is for the store-pack icon. Muse Spark Open is a Pilot option; on-screen credit: “Built with Muse Spark Open” in the studio footer. Usage table: {RESULT_USAGE_TABLE}.

## 2:50–3:00 — Close
The thesis is testable: a cheap model inside this harness versus a strong model without it. We report the numbers we have. We do not claim App Review outcomes.
