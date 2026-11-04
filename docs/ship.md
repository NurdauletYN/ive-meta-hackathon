# Ship to TestFlight

`harness ship <project_dir> --target testflight` builds a release IPA and uploads it to App Store Connect with the local App Store Connect API key. Credentials are read from the environment (or a path you set to a Keychain-exported `.p8`). They are never passed to a Pilot, never written into prompts, and are redacted from logs and `ship_report.json`.

This path is **unverified on a real device in this repository**. Tests use a fake subprocess runner. A real upload needs a Mac, Xcode, and an App Store Connect app record that already exists.

## One-time manual prerequisites (not automated)

Apple's public App Store Connect API cannot create app records. Do these once in the Apple UI:

1. Create the **app record** in App Store Connect (bundle id, name, SKU, primary language).
2. Create an App Store Connect **API key** with the **App Manager** role. Download the `.p8`. Store it outside the repo (or in macOS Keychain) and point `ASC_KEY_PATH` at it.
3. Sign in to **Xcode** with the Apple Developer team that owns the app (`APPLE_TEAM_ID`).
4. Add yourself (or the tester Apple ID) as an **internal TestFlight tester** on that app.

A **public** TestFlight link needs **Beta App Review**. That review, and App Review submission, are human steps. They are not part of `harness ship`.

## Environment

Copy `.env.example` to `.env` and set:

| Variable | Meaning |
| --- | --- |
| `ASC_KEY_ID` | Key id from App Store Connect |
| `ASC_ISSUER_ID` | Issuer id (UUID) |
| `ASC_KEY_PATH` | Absolute path to the `.p8` (gitignored) |
| `APPLE_TEAM_ID` | 10-character team id |
| `BUNDLE_ID` | Reverse-DNS id that already exists on the app record |

The `.p8` file must exist on disk. `harness ship` refuses with a clear message if any of these is missing.

## Commands

```bash
# Must be green first
uv run harness gate <project_dir> --build-web

# Print every command, validate inputs, execute nothing
uv run harness ship <project_dir> --target testflight --dry-run

# Build IPA and upload (live Apple call; not run in tests)
uv run harness ship <project_dir> --target testflight
```

`--dry-run` checks the env vars and that the `.p8` exists, then prints the `flutter build ipa` and `xcrun altool --upload-app` commands with key id and issuer redacted. It does not run the gate, does not edit the iOS project, and does not call Apple.

## What the live command does

1. Refuses unless `harness gate` is green (analyze, tests as configured, web build if you ran `--build-web`, preflight).
2. Sets bundle id, display name (from `lib/app/strings.dart` `appName`), version, and an auto-incremented build number in Info.plist, the Xcode project, and `pubspec.yaml`. The counter is `.ship-build-number` (gitignored).
3. Sets `ITSAppUsesNonExemptEncryption` to `false` in Info.plist.
4. Writes `ios/ExportOptions.plist` with `method` = `app-store-connect` and `teamID`.
5. Runs `flutter build ipa --release --export-options-plist=...`.
6. Uploads with `xcrun altool --upload-app --type ios -f <ipa> --apiKey $ASC_KEY_ID --apiIssuer $ASC_ISSUER_ID`.
7. Parses altool validation errors into readable lines.
8. Writes `ship_report.json` (steps, durations, IPA path, bundle id, version/build, outcome, parsed errors). All secret values redacted.

## What is automated vs not

**Automated after setup:** identity edits, encryption flag, export plist, IPA build, upload, error parsing, redacted report.

**Not automatable here:**

- Creating the App Store Connect app record (public API cannot create apps).
- Public TestFlight links (need Beta App Review).
- App Review submission.
- Signing identity / certificate issuance beyond “Xcode is signed into the team”.
- Predicting App Review outcomes. A green gate and a successful upload are not an approval.

## Secrets

`.gitignore` covers `*.p8`, `GoogleService-Info.plist`, `google-services.json`, `firebase_options.dart`, and `.ship-build-number`. Gitleaks scans for PEM private-key blocks. Do not paste keys into chat or into a Pilot prompt.
