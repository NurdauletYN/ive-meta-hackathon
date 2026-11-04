"""Build a store zip: icon (raw + 1024 + 512 Lanczos), listing, privacy draft."""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from meta_client.images import resize_lanczos_to_square
from pilot.fake import FakePilot
from pilot.protocol import Usage
from pilot.session import PilotSession
from pilot.usage_log import append_usage

from .launcher_icons import Runner, apply_launcher_icons
from .scan import read_app_name, scan_app

LISTING_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "subtitle": {"type": "string"},
        "description": {"type": "string"},
        "keywords": {"type": "string"},
    },
    "required": ["name", "subtitle", "description", "keywords"],
    "additionalProperties": False,
}

PRIVACY_LABEL = "template, not legal advice"
PRIVACY_HEADER = (
    "TEMPLATE, NOT LEGAL ADVICE. This draft is generated from what the app's code "
    "appears to contain. Have a lawyer review it before you ship.\n\n"
)

ImageFn = Callable[[str], bytes]


def mock_icon_png(size: int = 64) -> bytes:
    """Offline placeholder icon. Not a Muse Image output."""
    buf = io.BytesIO()
    Image.new("RGB", (size, size), (21, 101, 192)).save(buf, format="PNG")
    return buf.getvalue()


def fake_listing(app_name: str) -> dict[str, str]:
    return {
        "name": app_name,
        "subtitle": "A capsule-built utility app.",
        "description": (
            f"{app_name} listing copy generated offline by FakePilot from a project scan. "
            "Not a live model output."
        ),
        "keywords": "utility,app",
    }


def _privacy_body(facts: dict[str, Any]) -> str:
    lines = ["# Privacy policy draft", "", PRIVACY_HEADER]
    if facts.get("auth"):
        lines.append("- The app has account sign-in. Email may be stored to identify the user.")
    else:
        lines.append("- No auth interface was detected in lib/.")
    if facts.get("account_deletion"):
        lines.append("- The app exposes in-app account deletion.")
    if facts.get("billing"):
        lines.append("- The app has a billing/restore-purchases interface (subscriptions may apply).")
    else:
        lines.append("- No billing interface was detected in lib/.")
    perms = facts.get("permissions") or []
    if perms:
        lines.append("- Declared iOS usage strings: " + ", ".join(perms) + ".")
    else:
        lines.append("- No camera/photos/microphone/location usage strings were found.")
    lines.append("")
    lines.append("This paragraph is a template. It is not a legal document.")
    lines.append("")
    return "\n".join(lines)


def muse_image_fn(session: PilotSession) -> ImageFn:
    """Live Muse Image generate, logged to the same usage.jsonl as the Pilot. Respects --max-usd."""

    def generate(prompt: str) -> bytes:
        from dataclasses import replace

        from meta_client import MetaClient, MuseImage, load_settings
        from meta_client.pricing import image_cost_usd

        if session.budget is not None:
            session.budget.check()
        settings = replace(load_settings(), usage_log=None)
        client = MetaClient(settings)
        try:
            images = MuseImage(client).generate(prompt, size="1024x1024", n=1)
        finally:
            client.close()
        last = client.usage.records[-1] if client.usage.records else None
        model = last.model if last is not None else "muse-image-1.0"
        cost = last.est_cost_usd if last is not None else image_cost_usd(model, 1)
        append_usage(
            session.usage_path,
            run_id=session.run_id,
            pilot="muse-image",
            stage="storepack_icon",
            usage=Usage(
                input_tokens=0,
                cached_tokens=0,
                output_tokens=0,
                latency_ms=last.latency_ms if last is not None else 0.0,
                est_cost_usd=cost,
            ),
            model=model,
        )
        if session.budget is not None:
            session.budget.check()
        return images[0].data

    return generate


def build_storepack(
    project: Path,
    out_dir: Path,
    *,
    session: PilotSession | None = None,
    image_fn: ImageFn | None = None,
    app_name: str | None = None,
    icon_mock: bool | None = None,
    launcher_runner: Runner | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    name = app_name or read_app_name(project)
    facts = scan_app(project)
    listing = fake_listing(name)
    if session is not None:
        listing = session.complete_json(
            (
                "Return App Store listing copy as JSON. Use only features present in the scan. "
                "Do not invent permissions, analytics, or data collection the app does not have. "
                "Do not include API keys, tokens, or file paths."
            ),
            f"App name: {name}\nDetected features: {json.dumps(facts)}",
            LISTING_SCHEMA,
            "storepack",
        )
    listing_path = out_dir / "listing.json"
    listing_path.write_text(json.dumps(listing, indent=2) + "\n", encoding="utf-8")
    privacy = _privacy_body(facts)
    privacy_path = out_dir / "privacy.md"
    privacy_path.write_text(privacy, encoding="utf-8")

    files = [listing_path, privacy_path]
    mock = True if icon_mock is None else icon_mock
    icon_meta: dict[str, Any] = {"skipped": True, "mock": True}
    if image_fn is not None:
        prompt = f"Flat rounded-square app icon for {listing.get('name') or name}, no text, simple motif."
        raw = image_fn(prompt)
        raw_path = out_dir / "icon_raw.png"
        raw_path.write_bytes(raw)
        png_1024, w, h = resize_lanczos_to_square(raw, 1024)
        png_512, w512, h512 = resize_lanczos_to_square(raw, 512)
        p1024 = out_dir / "icon_1024.png"
        p512 = out_dir / "icon_512.png"
        p1024.write_bytes(png_1024)
        p512.write_bytes(png_512)
        files.extend([raw_path, p1024, p512])
        icon_meta = {
            "skipped": False,
            "mock": mock,
            "raw": raw_path.name,
            "1024": [w, h],
            "512": [w512, h512],
            "launcher_icons": apply_launcher_icons(
                project, p1024, runner=launcher_runner
            ),
        }

    zip_path = out_dir / "storepack.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, path.name)
    return {
        "ok": True,
        "zip": str(zip_path),
        "facts": facts,
        "listing": listing,
        "icon": icon_meta,
        "privacy_label": PRIVACY_LABEL,
        "app_name": name,
    }


def canned_fake_pilot(app_name: str) -> FakePilot:
    fake = FakePilot()
    fake.enqueue("storepack", fake_listing(app_name))
    return fake
