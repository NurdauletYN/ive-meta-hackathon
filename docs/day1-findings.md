# Day 1 findings

Run date: 2026-10-30. Models: `muse-spark-1.3`, `sam-3.1`, `muse-image-1.0` (Standard mode).
Raw outputs: `ivebench/results/day1/`. Per-call usage (tokens, latency, cost): `ivebench/results/usage.jsonl`.

## Results

| Check | Result | Numbers |
| --- | --- | --- |
| (a) File-ops JSON, 10 runs | **PASS** | 10/10 schema-valid, 10/10 exact expected ops. Median latency 5.9 s. Cost $0.062 for 10 runs. |
| (b) Sketch as image input | **PASS** (accepted: yes; read: yes) | Accepted on 3/3 sketches. Type recall: login 1.00, products 1.00, settings 0.67. |
| (c) SAM 3.1 on sketches | **FAIL** | 0 masks for every concept on every synthetic sketch (0/9 expected types found). No API errors. |
| (d) Muse Image 1024×1024 icon | **FAIL** (size) | Image generated and saved (`icon_1024.png`), but it decodes to **1600×1600**. |

## Surprises and what they mean

1. **SAM returns nothing on line-drawn wireframes.** The pipeline itself works: the same SAM call on a public
   photo (`ducks.jpg`, "duck") returned 5 masks, matching the cookbook's own run. The same code returned zero
   masks for "button", "text field", "image" and "card" on the synthetic wireframes, and zero for "phone"
   on the generated icon. Both streaming and non-streaming requests returned an empty `output_text` (checked on login.png / "button"), and the
   usage block reports `images_processed: 1` with zero tokens. So SAM ran and found nothing. It is not a
   parsing bug. **This is the most important finding for the sketch pipeline:** SAM 3.1 as a concept
   segmenter does not detect UI elements drawn as thin lines. Options are in "Decisions needed" below.
2. **An empty SAM result is indistinguishable from "no match".** Both are a valid completed response with
   empty text. The adapter can't tell "nothing matched" apart from "the model didn't see the element".
   The usage log records `images: 1` either way, so billing is clear, but quality checks need a positive control
   (like the duck photo) in every run.
3. **Muse Image ignores the requested pixel size.** `size: "1024x1024"` came back as 1600×1600. The docs say
   `size` is an aspect ratio only, and this confirms it. The store listing needs an exact 1024, so the
   icon needs a local resize or a different request before it ships.
4. **Structured output is reliable on this prompt.** 13 of 13 structured calls returned valid JSON (10 in (a),
   3 in (b)). Muse Spark's per-call cost is about $0.007, and reasoning tokens are most of the output.
5. **Image input works.** The API accepted all sketches. The model listed buttons, text fields and images
   correctly, and it also added some `other` entries that aren't in the expected set (e.g. the price tags).

## Latency and cost (today's runs)

| Op | Calls | Median latency | Total cost |
| --- | --- | --- | --- |
| `text.structured` (a, b) | 13 | 5.9 s | $0.087 |
| `text.generate` (key check) | 1 | 2.8 s | $0.001 |
| `sam.segment_image` (c, plus 2 probes) | 14 | 1.2 s | $0.035 |
| `image.generate` (d) | 1 | 20.2 s | $0.010 |

Total: 29 calls, $0.134. Costs are estimates from the pricing page (Standard mode). Two of them are not
verified against the invoice yet: whether `cached_tokens` is inside `input_tokens`, and whether a SAM call
with zero matches is billed. The SAM probe calls are in the usage log but not in the scripts' own summaries.

## Reproducibility

- No `seed` is sent. The docs don't document one for Muse Spark, and the image docs say an unknown
  `seed` field returns 400. So the 10 file-ops runs are not bit-reproducible. The saved raw outputs are the record.
- The synthetic sketches are deterministic (fixed seed, identical PNG hashes on re-run; a test checks this).

## Caveats

- **The sketches are synthetic stand-ins**, not photos of hand-drawn sketches. Result (c) in particular
  may change with real photos, which have shading, paper texture, and thicker strokes. Replace them
  (see `scripts/day1/README.md`) before quoting (b) or (c) anywhere.
- Pass thresholds were chosen before running: (a) ≥ 9/10 exact matches; (b) every sketch accepted and recall ≥ 0.5;
  (c) every expected type ≥ 1 mask; (d) exact 1024×1024.

## Decisions needed

1. **SAM on sketches (c).** Options:
   - (A) Try a quick preprocessing experiment: thicken strokes and fill element interiors, then re-run (c). About 12 calls, about $0.03.
   - (B) Test real hand-drawn photos first, since they are the actual input.
   - (C) Drop SAM for line sketches and get boxes from Muse Spark, keeping SAM for photos of real objects.
2. **Icon size (d).** Options:
   - (A) Resize the 1600×1600 output locally to 1024×1024 for the store pack. Keep the raw file. (Recommended.)
   - (B) Keep 1600 and resize only when the store pack is built.
   - (C) Try other size strings before settling on either.

## Not done yet (blocked)

- GitHub: `gh` is logged out for NurdauletYN (the stored token is invalid). The repo is not created or pushed,
  and no PRs are open. Run `gh auth login -h github.com`, then the repo can be created as a private repo.
- Tags (`v0.1-eval` etc.) come after the eval harness exists.
- LICENSE: pending the organizers' answer. The SAM License on `meta-sam-parser` also has to be considered in that decision.
