# storepack

`harness storepack` builds a zip of App Store listing inputs from a Flutter project:

- listing copy (Pilot JSON: name, subtitle, description, keywords)
- a privacy-policy **template, not legal advice**, drafted from a scan of auth, billing, and iOS usage strings
- app icon: raw Muse Image bytes plus Lanczos 1024×1024 and 512×512 copies

Offline: `--pilot fake` uses FakePilot and a placeholder PNG (mock, not Muse Image).
Live: `--pilot muse --max-usd 1` uses Muse Spark for copy and Muse Image for the icon.

See `docs/storepack.md`.
