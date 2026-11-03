# Local harness tester

A small dashboard, written this week, so you can drive **design / build / gate** without the private Ive product.

```bash
uv run harness ui --port 8765
# open http://127.0.0.1:8765/
```

Start with **Pilot = fake** (canned JSON, no API spend). Switch to **muse** only with a `--max-usd` cap. Flutter web builds are off unless you tick the box.

Auth and billing in the capsule are in-memory mocks. Preflight is not legal advice.
