# 3-minute demo: outline of what the video shows

Before this week there was no public Rocket repo: no capsule, no Pilot layer, no studio, no gate. Everything in this repository was written during the Meta Global AI Developer Hackathon (Oct 27 – Nov 4 2026). The private Ive product is not in the video.

## 0:00–0:20 — What it is
Rocket is a model-agnostic harness. The harness is the rocket. The model is the pilot. You describe an app in a chat; the harness builds inside a locked Flutter capsule, then verifies with a deterministic gate.

## 0:20–0:50 — Studio
The studio runs locally (`uv run harness ui --port 8765`). Type an idea. Muse Spark returns the app's data; the harness writes the screens from the design kit; the Flutter web preview loads in the phone frame. Follow-up messages improve the same app, and each change is saved as a version that can be restored or downloaded as code.

Capsule auth and billing are in-memory mocks unless the user supplies config. That is labeled demo mode.

## 0:50–1:20 — What the harness constrains
`lib/core/` is protected and `lib/app/` is editable. The guard rejects writes to core. The model does not write page layout: it returns catalog JSON and the kit screens render it. Gate: analyze, tests, web build, 15 preflight checks. Repair is at most two rounds, fed only by gate failures.

## 1:20–1:50 — Evidence, and what is not claimed
The harness-vs-no-harness comparison is implemented (`harness sweep`, `harness report`) but no published result exists, so `ivebench/results/results.md` is 0/0 and the video makes no comparative claim. What the video shows instead: the gate report for the build on screen, the spend from `usage.jsonl` (`METAUSE.md`), and the small live quality check in `docs/quality_check.md`.

Limits stated on screen: small idea set, mock auth and billing, preflight pass rates are not Apple rejection rates.

## 1:50–2:20 — Ship path (unverified live)
`harness ship --dry-run`. Credentials never go to a model. There is no live TestFlight upload in this repo, so it is described as unverified; no store listing is implied.

## 2:20–2:50 — Meta models
Muse Spark (`muse-spark-1.3`) designs the look and returns the app data. Muse Image generated the store icon and the bundled product photos. Muse Spark Open is a selectable Pilot, but the usage log has no live calls for it, so it is not credited as used. The studio footer names the model that actually built the app.

## 2:50–3:00 — Close
The thesis is testable: a cheap model inside this harness versus a strong model without it. We report the numbers we have, which is none yet for that comparison. We do not claim App Review outcomes.
