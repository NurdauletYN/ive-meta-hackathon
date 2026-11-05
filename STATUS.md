# Status — 2026-11-05

Deadline: Thu Nov 5, 07:00 UTC+5 (Wed Nov 4, 9:00 PM ET).

Track: Indie / Push the Frontier. Standalone repo: https://github.com/NurdauletYN/ive-meta-hackathon. **Not** the private Ive product.

All work is on `main`, merged through PRs with merge commits (#1–#34 plus the submission-docs PR). Tag for the submission: `v1.2-submission`.

## What is done

| Area | What landed |
| --- | --- |
| Capsule | Flutter template, protected `lib/core/`, editable `lib/app/`, feature registry |
| Guard + gate | File-op guard; `flutter analyze`, `flutter test`, optional web build, **15 preflight checks** (see `docs/preflight.md`) |
| Pilot | `complete_json`, Fake / Muse Spark / Muse Spark Open (config-gated), `--max-usd`, `usage.jsonl` |
| Build modes | `harness`, `bare`, `scaffold_only`; up to 2 gate-driven repair rounds |
| Studio chat | One text field: first message builds, later messages improve the same app; live steps and cost; offline demo mode |
| Projects and versions | `meta.json` per run, projects sidebar, version chips (restore forks), code download zip without secrets |
| Design engine | 11 curated palettes (WCAG AA, light and dark), palette from the idea or an instruction, kit v2 widgets, fonts, 24 Muse Image photos |
| Kit | Token-driven widgets in `lib/core/kit/` (protected), floating tab bar, `KitShopScreen` / `KitDetailScreen` / `KitProfileScreen` / `KitAuthScreen`; API in `docs/kit_api.md` |
| Catalog writer | Harness-mode Muse output is `AppCatalog` JSON; `src/harness/kit_writer.py` writes the Dart screens, so the model does not write layout |
| Preflight | `no_raw_material` is a hard FAIL on stock Material chrome; `kit_usage` and `not_text_only` stay WARN |
| Studio hygiene | Build fingerprint in the header (`/api/studio`), scroll lock so the preview cannot scroll the page, footer credits the model that actually ran |
| Sweep / report | Infra vs quality classification, resume, dirty-tree refusal, counts-only `harness report` and `--html`, sameness, `usage-report` |
| Ship | `harness ship --target testflight` (fake-runner tests; no live Apple call) |
| Store pack | Listing copy, privacy template, Muse Image icon, `flutter_launcher_icons` |
| Adapters | Config-gated Firebase auth and RevenueCat billing with fake-gateway tests |
| Docs / hygiene | VISION, README, METAUSE (generated usage block), VIDEO_SCRIPT, `scripts/prepublish_check.sh`, LICENSE (MIT) |

## Results

- **Harness vs no harness: implemented, not published.** `harness sweep` and `harness report` work and are tested with FakePilot. `ivebench/results/results.md` is **0/0**: there is no classified sweep JSON in git. The untracked local `ivebench/results/sweep/` is not a published result (several bare arms are timeouts, which are infrastructure, not quality). No comparative claim is made.
- **Small live quality check**: 3 Muse Spark harness builds, $1.50 cap, all 3 completed builds passed the gate (`docs/quality_check.md`). It predates the catalog writer.
- **Usage**: see the generated table in `METAUSE.md` (from `ivebench/results/usage.jsonl`, FakePilot rows excluded). It is spend, not quality.
- **Muse Spark Open**: no live calls in the usage log. It is not credited as used.

## Limits and unverified

- No published harness-vs-bare comparison; small idea set (8 ideas).
- Auth and billing are in-memory mocks unless config is supplied; Firebase and RevenueCat adapters are unverified on a device or sandbox purchase.
- Live TestFlight upload is unverified (fake subprocess in tests).
- Privacy text is a template, not legal advice. Preflight pass rates are not Apple rejection rates.
- The studio is local (127.0.0.1) and does not run storepack or ship.

## Submission hygiene

`bash scripts/prepublish_check.sh` (gitleaks over history, secret filenames, PEM and key patterns, tests, gate with web build, README links, fresh-clone reproduce) is the last check before tagging.

## Human-only items

- Repo visibility (public) and logged-out verification.
- Claim Meta credits; rotate any key that was pasted in chat.
- Contributors listed on the submission page; the representative submits.
