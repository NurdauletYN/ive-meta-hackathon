# Rocket studio

Local tester, written this week. Not the Ive product.

```bash
uv run harness ui --port 8765
# http://127.0.0.1:8765/
```

- **3 directions** — Muse (or FakePilot) proposes three token sets. Click a phone to pick it.
- **Build harness** — spec + guarded file ops + gate. Optional Flutter web preview in the phone frame.
- **Compare bare** — same prompt, capsule vs blank `flutter create`, two phones.

Start with Pilot = fake. Turn on **web preview** only when you want `flutter build web` (~13s). Muse spends the `--max-usd` cap.
