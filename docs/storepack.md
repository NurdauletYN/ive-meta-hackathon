# Store pack

`harness storepack <project_dir> --pilot fake|muse --out <dir> --max-usd 1` writes a zip of store-listing inputs next to the generated app.

## What is in the zip

| File | Source |
| --- | --- |
| `listing.json` | Pilot `complete_json` (name, subtitle, description, keywords) from a scan of the project |
| `privacy.md` | Template drafted from detected auth, billing, account deletion, and iOS usage strings. Labeled **template, not legal advice**. |
| `icon_raw.png` | Bytes returned by Muse Image (or a mock PNG in FakePilot mode) |
| `icon_1024.png` | Local Lanczos resize of the raw bytes to 1024×1024 |
| `icon_512.png` | Local Lanczos resize of the raw bytes to 512×512 |

The scan looks at `lib/**/*.dart` and `ios/Runner/Info.plist`. It does not call Apple, Firebase, or RevenueCat.

## Commands

Offline (no API key):

```bash
uv run harness storepack flutter_template --pilot fake --out runs/storepack-offline
```

Live smoke (Muse Spark listing + one Muse Image icon). Requires `META_API_KEY`. Do not paste the key into chat.

```bash
uv run harness storepack flutter_template --pilot muse --max-usd 1 --out runs/storepack-smoke
```

Credentials are never passed to the Pilot prompt. `--max-usd` covers listing tokens and the image call (logged to `ivebench/results/usage.jsonl`).

## What is unverified

- The listing copy is a draft. It is not an App Store submission.
- The privacy file is a **template, not legal advice**. It is not a lawyer-reviewed policy.
- Muse Image output size may differ from the requested `1024x1024`; that is why the raw file is kept and the 1024/512 copies are resized locally. This path is **unverified** as a real App Store icon until uploaded through App Store Connect.
- FakePilot icons are mock PNGs, not Muse Image.

## What this does not do

It does not create an App Store Connect app record, upload screenshots, or submit for App Review. See [docs/ship.md](ship.md) for TestFlight upload.
