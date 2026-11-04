# Rocket: the end product

## One sentence
Rocket is a model-agnostic harness that turns an app idea into a verified, store-ready Flutter app and ships it to TestFlight under the user's own developer account. The harness is the rocket. The model is the pilot.

## The problem
Building the app is no longer the hard part. Everything around it is: auth, onboarding, paywall, privacy and terms screens, account deletion, store metadata, signing, upload. Every app repeats the same plumbing, and every repetition brings the same bugs. Founders who only want to think about the idea, the design and the UX end up fighting store rules instead. (Market context: see README section "Why this exists".)

## The user
A non-technical founder or an indie developer who wants to say "I want an app for X", choose a look, and get a working app on their phone, without touching auth, billing, legal screens or signing.

## Core thesis (testable)
A well-built harness reduces the decisions a model can get wrong, so a cheap model inside the harness ships what a strong model without it cannot. We test this, we do not assume it. Results are reported honestly, with infrastructure failures kept separate from quality failures.

## Principles
1. Constrain the pilot: protected core files, schema-validated outputs, guarded file operations. The model edits only the editable surface.
2. Verify deterministically: analyze, tests, web build, store-compliance preflight. The gate decides, not a model.
3. Model-agnostic: any model that can emit JSON is a pilot. Meta models are the primary pilots.
4. Measure everything: cost per shippable app, repair rounds, cached tokens, latency.
5. Credentials never reach a model. The harness holds them locally, reads them from environment or Keychain, and redacts them from all logs.
6. Honest claims only. Anything not verified on a real device or a real service is labeled mock or unverified.

## Pipeline
Idea -> Looks (3 distinct design directions as validated design tokens, chosen by the user) -> Spec (app name, onboarding copy, paywall copy, screens, data models) -> Build (guarded file operations inside the capsule) -> Gate (analyze, tests, web build, preflight) -> Repair (up to 2 rounds, fed only by gate failures) -> Store pack (icon, listing copy, privacy policy draft) -> Ship (build IPA, upload to App Store Connect, appears in TestFlight).

## What is automated and what is not
Automated: everything above after setup. Not automatable: creating the App Store Connect app record (Apple's public API cannot create apps), public TestFlight links (need Beta App Review), App Review submission. These are one-time or human steps and are documented in docs/ship.md.

## The capsule
A fresh Flutter foundation with a protected core (router, auth interface, billing interface, onboarding scaffold, legal screens, settings with account deletion, paywall with subscription disclosure) and an editable surface (design tokens, features, strings). Real Firebase and RevenueCat adapters sit behind the same interfaces and are enabled only when the user supplies configuration.

## Success metrics
- Shippable-app rate (passes the full gate) per pilot, with and without the harness
- Cost per shippable app and median repair rounds per pilot
- Cross-model gap: how much the harness narrows the gap between cheap and strong pilots
- Evidence of a real device: a generated app installed through TestFlight

## Non-goals
No public hosted service, no handling of other people's credentials on a server, no claim to predict App Review outcomes. Preflight pass rates are not Apple rejection rates.

## Long term
Rocket becomes the verify-and-ship layer under Ive: validate an idea, build it, verify it, ship it, using whichever model is best at the moment, with a cloud macOS builder replacing the local Mac for hosted use.
