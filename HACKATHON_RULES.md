# Meta Global AI Developer Hackathon: rules for any model working in this repo

Building period: Oct 27 – Nov 4, 2026. Submission due Wed Nov 4, 9:00 PM ET
(= Nov 5, 07:00 UTC+5). Late submissions are not considered.

## Hard rules (violation = disqualification)

1. Repo must be PUBLIC at submission.
2. New work only. Everything shown must be built during the event. The demo must
   clearly identify what was built during the hackathon. Never copy, import, or
   reference the private Ive repo. If reuse seems necessary, stop and ask.
3. Max team size 4. Everyone who contributed is listed on the submission page.
4. No code, data, or assets we lack rights to. Respect license terms.
5. Must use Meta models via Meta Model API and/or open weights
   (Muse Spark series, Muse Wonder, Muse Image, Muse Voice Transcribe, SAM 3.1,
   Muse Glimmer, Muse Spark Open, Muse Code). Standard mode only, never Contributor.
6. Baseten model id for the hackathon is `meta-models/muse-spark-open-1026`
   (not `meta-models/muse-spark-open`).

## Banned or anti-project topics (never build or generate)

Medical or mental-health advice, skin/blemish detectors, AI job-application
screeners, nutrition coaches, personality analyzers, sports analyzers/coaches,
anything political or about war, basic RAG apps, simple image analyzers, simple
"AI for education" chatbots. Eval ideas must avoid all of these.

## Submission checklist

- [ ] Public repo, logged-out access verified
- [ ] 3-minute demo video, link verified, shows only hackathon-built work
- [ ] README: NEW vs PRE-EXISTING table, 5-minute reproduce steps, results table
- [ ] HACKATHON_SCOPE.md and METAUSE.md current
- [ ] Contributors listed; one Representative submits one project
- [ ] Credits claimed individually by Nov 4, 9 PM ET (Meta $150; Baseten/Modal/Fireworks optional)

## Judging (stages)

1. Pass/fail: fits a problem statement ("Build for Your World" or "Push the Frontier")
   and reasonably uses Meta models.
2. Scored 0–10 on the official rubric. TODO: paste the rubric table here.
3. Top 5 per track: judges watch demo videos live and rank them.

## Engineering rules for this repo

- Never commit secrets. `.env` is gitignored; keep `.env.example` current.
- All Meta calls go through `src/meta_client` or `src/pilot` with retries, timeouts,
  and usage logging (tokens, cached tokens, latency, cost). Do not guess model
  IDs, endpoints, or request shapes; verify against [dev.meta.ai docs](https://dev.meta.ai/docs/quickstart) or ask.
- Any number we publish must be reproducible: fixed inputs, raw outputs saved in
  `ivebench/results/`, cost taken from `usage.jsonl`.
- Report failures honestly (n, mocks, timeouts). Never present a rigged or
  path-biased comparison as a result.
- Small commits, feature branches, merge-commit PRs. Update `HACKATHON_SCOPE.md`
  when a module is added. No features outside the current task; ask first.
- Tests cover failure paths. Offline tests use FakePilot; live calls need an
  explicit cost cap (`--max-usd`).
