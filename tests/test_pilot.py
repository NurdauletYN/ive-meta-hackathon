"""Offline Pilot-layer tests: FakePilot e2e, budget, guard, schema retries."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from harness.build import run_build
from harness.cli import main
from harness.design import pick_direction, run_design
from harness.diversity import diversity_errors, hex_hue, hue_delta
from harness.gate import GateReport, StepResult
from harness.prompts import CAPSULE_PREFIX
from meta_client.errors import MetaAuthError
from pilot.config import load_pilot
from pilot.fake import FakePilot
from pilot.muse import MuseSparkPilot
from pilot.openai_compat import OpenAICompatPilot, from_env
from pilot.protocol import BudgetExceeded
from pilot.session import PilotSession
from preflight.types import CheckResult, CheckStatus

ROOT = Path(__file__).resolve().parents[1]
CAPSULE = ROOT / "flutter_template"


def _write(path: str, content: str) -> dict:
    return {"op": "write", "path": path, "content": content, "find": None, "replace": None}


def _pairs(*rows: tuple[str, str, str]) -> list[dict]:
    return [{"name": n, "foreground": fg, "background": bg} for n, fg, bg in rows]


def _tokens(primary: str, *, radius: float, typography: str, on_primary: str = "#FFFFFF") -> dict:
    surface, on_surface = "#F5F7FA", "#1A1A1A"
    return {
        "colors": {
            "primary": primary,
            "on_primary": on_primary,
            "surface": surface,
            "on_surface": on_surface,
        },
        "contrast_pairs": _pairs(
            ("body", on_surface, surface),
            ("cta", on_primary, primary),
        ),
        "corner_radius": radius,
        "typography": typography,
    }


def _direction(name: str, primary: str, *, radius: float, typography: str) -> dict:
    return {
        "name": name,
        "rationale": f"{name} direction for the gallery.",
        "tokens": _tokens(primary, radius=radius, typography=typography),
    }


GOOD_DIRECTIONS = {
    "directions": [
        _direction("Harbor", "#1565C0", radius=8, typography="default"),
        _direction("Ember", "#C62828", radius=16, typography="compact"),
        _direction("Grove", "#2E7D32", radius=24, typography="expressive"),
    ]
}

SAME_HUE_DIRECTIONS = {
    "directions": [
        _direction("Bay", "#1565C0", radius=12, typography="default"),
        _direction("Navy", "#1976D2", radius=12, typography="default"),
        _direction("Ink", "#0D47A1", radius=12, typography="default"),
    ]
}

REPLACEMENT = {
    "direction": _direction("Coral", "#C62828", radius=24, typography="expressive"),
}

APP_SPEC = {
    "app_name": "Tool Library",
    "bundle_id": "com.example.toollib",
    "onboarding": [
        {"title": "Share", "body": "List tools neighbors can borrow."},
        {"title": "Borrow", "body": "Request a tool and pick it up."},
        {"title": "Return", "body": "Mark it back when you are done."},
    ],
    "paywall_title": "Plus",
    "paywall_body": "Unlimited borrows for your block.",
    "paywall_cta": "Subscribe",
    "screens": [
        {"id": "catalog", "purpose": "browse tools", "fields": [{"name": "title", "type": "string"}]}
    ],
    "data_models": [{"name": "Tool", "fields": [{"name": "title", "type": "string"}]}],
}

NOTES_DART = """import 'package:flutter/material.dart';

class NotesScreen extends StatefulWidget {
  const NotesScreen({super.key});
  @override
  State<NotesScreen> createState() => _NotesScreenState();
}

class _NotesScreenState extends State<NotesScreen> {
  final items = <String>['Hammer'];
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notes')),
      body: ListView(
        children: [
          for (final item in items) ListTile(title: Text(item)),
          TextButton(onPressed: () => setState(() => items.add('Saw')), child: const Text('Add')),
        ],
      ),
    );
  }
}
"""

REGISTRY_DART = """import 'package:flutter/material.dart';
import 'notes/notes_screen.dart';

class FeatureRoute {
  const FeatureRoute({
    required this.path,
    required this.label,
    required this.builder,
  });

  final String path;
  final String label;
  final WidgetBuilder builder;
}

List<FeatureRoute> extraFeatureRoutes() {
  return [
    FeatureRoute(path: '/notes', label: 'Notes', builder: (c) => const NotesScreen()),
  ];
}
"""

GOOD_OPS = {
    "operations": [
        _write("lib/app/features/notes/notes_screen.dart", NOTES_DART),
        _write("lib/app/features/registry.dart", REGISTRY_DART),
    ]
}

PROTECTED_OPS = {
    "operations": [_write("lib/core/auth/auth_service.dart", "void hack() {}")]
}

BARE_MAIN = """import 'package:flutter/material.dart';

void main() {
  runApp(const MaterialApp(home: Text('Tool Library')));
}
"""

BARE_OPS = {"operations": [_write("lib/main.dart", BARE_MAIN)]}


def _session(pilot: FakePilot, tmp_path: Path, run_id: str, max_usd: float | None = None) -> PilotSession:
    return PilotSession(pilot, run_id=run_id, usage_path=tmp_path / "usage.jsonl", max_usd=max_usd)


def _pass_gate(project: Path) -> GateReport:
    return GateReport(
        project_dir=str(project),
        ok=True,
        steps=[
            StepResult("flutter_analyze", True, 1.0),
            StepResult("flutter_build_web", True, 1.0),
            StepResult("preflight", True, 1.0),
        ],
        preflight=[],
    )


def _stub_build(_project: Path) -> tuple[bool, str]:
    return True, "skipped"


def test_hue_delta_wraps_around() -> None:
    assert hue_delta(10, 350) == 20
    assert abs(hex_hue("#FF0000") - 0.0) < 1.0


def test_diversity_rejects_close_hues() -> None:
    from pilot.schemas import DirectionsPlan

    plan = DirectionsPlan.model_validate(SAME_HUE_DIRECTIONS)
    errors = diversity_errors(list(plan.directions))
    assert errors


def test_invalid_design_json_retries_then_succeeds(tmp_path: Path) -> None:
    fake = FakePilot()
    fake.enqueue("design", {"directions": []}, GOOD_DIRECTIONS)
    session = _session(fake, tmp_path, "design-invalid")
    result = run_design(
        "tool library",
        session,
        capsule=CAPSULE,
        out_dir=tmp_path / "out",
        build_fn=_stub_build,
    )
    assert len(result["directions"]) == 3
    assert result["diversity_ok"]
    assert result["contrast_ok"]
    assert (tmp_path / "out" / "gallery.html").is_file()
    assert fake.calls[0][0] == "design"
    assert fake.calls[1][0] == "design"
    assert "failed validation" in fake.calls[1][2]


def test_design_regenerates_one_direction_when_diversity_fails(tmp_path: Path) -> None:
    fake = FakePilot()
    fake.enqueue("design", SAME_HUE_DIRECTIONS)
    fake.enqueue("design_regenerate", REPLACEMENT)
    session = _session(fake, tmp_path, "design-div")
    result = run_design("tool library", session, capsule=CAPSULE, out_dir=tmp_path / "out", build_fn=_stub_build)
    names = [d["name"] for d in result["directions"]]
    assert names[2] == "Coral"
    assert any(c[0] == "design_regenerate" for c in fake.calls)


def test_design_pick_writes_choice(tmp_path: Path) -> None:
    fake = FakePilot()
    fake.enqueue("design", GOOD_DIRECTIONS)
    session = _session(fake, tmp_path, "pick")
    out = tmp_path / "out"
    run_design("idea", session, capsule=CAPSULE, out_dir=out, build_fn=_stub_build)
    path = pick_direction(out, 2)
    choice = json.loads(path.read_text(encoding="utf-8"))
    assert choice["n"] == 2
    assert choice["direction"]["name"] == "Ember"


def test_budget_abort_after_usage_crosses_cap(tmp_path: Path) -> None:
    fake = FakePilot(cost_per_call=1.0)
    fake.enqueue("spec", APP_SPEC, APP_SPEC)
    session = _session(fake, tmp_path, "budget-1", max_usd=1.5)
    session.complete_json("sys", "one", {}, "spec")
    with pytest.raises(BudgetExceeded) as exc:
        session.complete_json("sys", "two", {}, "spec")
    assert exc.value.run_id == "budget-1"
    assert exc.value.spent >= 1.5
    lines = (tmp_path / "usage.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    row = json.loads(lines[0])
    assert row["run_id"] == "budget-1"
    assert row["pilot"] == "fake"
    assert row["stage"] == "spec"


def test_cli_maps_budget_exceeded_to_exit_3(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def boom(_args: object) -> None:
        raise BudgetExceeded("r1", 4.0, 3.0)

    monkeypatch.setattr("harness.cli._dispatch", boom)
    with pytest.raises(SystemExit) as ei:
        main(["gate", str(CAPSULE)])
    assert ei.value.code == 3
    err = capsys.readouterr().err
    assert "budget_exceeded" in err


def test_openai_compat_from_env_refuses_without_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_COMPAT_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_COMPAT_API_KEY", raising=False)
    with pytest.raises(MetaAuthError):
        from_env()


def test_openai_compat_mock_http() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["model"] == "meta-models/muse-spark-open-1026"
        assert body["messages"][0]["content"].startswith("SYS")
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps({"hello": "world"})}}],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 3,
                    "prompt_tokens_details": {"cached_tokens": 2},
                },
            },
        )

    pilot = OpenAICompatPilot(
        base_url="https://example.invalid/v1",
        model="meta-models/muse-spark-open-1026",
        api_key="sk-test",
        transport=httpx.MockTransport(handler),
    )
    obj, usage = pilot.complete_json("SYS", "USER", {"type": "object"}, "spec")
    assert obj == {"hello": "world"}
    assert usage.cached_tokens == 2
    assert usage.input_tokens == 11


def test_muse_spark_pilot_puts_system_prefix_first(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    class Spark:
        model = "muse-spark-1.3"

        def generate_structured(self, prompt: str, schema: dict, schema_name: str) -> object:
            captured["prompt"] = prompt
            captured["schema_name"] = schema_name
            return SimpleNamespace(data={"ok": True}, raw={})

    def fake_init(self, client=None) -> None:  # noqa: ANN001
        self._client = SimpleNamespace(usage=SimpleNamespace(records=[]))
        self._spark = Spark()
        self.model = Spark.model

    monkeypatch.setattr(MuseSparkPilot, "__init__", fake_init)
    obj, _usage = MuseSparkPilot().complete_json("SYSTEM", "user-var", {}, "file_ops")
    assert obj == {"ok": True}
    assert captured["prompt"] == "SYSTEM\n\nuser-var"
    assert captured["prompt"].startswith("SYSTEM")


def test_load_fake_pilot_from_yaml() -> None:
    pilot = load_pilot("fake", ROOT / "pilots.yaml")
    assert isinstance(pilot, FakePilot)


def test_harness_mode_e2e_and_identical_prefix(tmp_path: Path) -> None:
    fake = FakePilot(cached_tokens=128)
    fake.enqueue("spec", APP_SPEC)
    fake.enqueue("file_ops", GOOD_OPS)
    session = _session(fake, tmp_path, "h1")
    result = run_build(
        "tool_library",
        session,
        mode="harness",
        run_dir=tmp_path / "run",
        capsule=CAPSULE,
        gate_fn=_pass_gate,
        build_web=False,
    )
    assert result["ok"]
    assert result["mode"] == "harness"
    assert result["repair_rounds"] == 0
    assert result["tokens"]["cached"] == 256  # 128 logged on spec + file_ops
    written = json.loads((tmp_path / "run" / "result.json").read_text(encoding="utf-8"))
    assert written["pilot"] == "fake"
    notes = tmp_path / "run" / "project" / "lib" / "app" / "features" / "notes" / "notes_screen.dart"
    assert notes.is_file()
    assert "StatefulWidget" in notes.read_text(encoding="utf-8")
    strings = (tmp_path / "run" / "project" / "lib" / "app" / "strings.dart").read_text(encoding="utf-8")
    assert "Tool Library" in strings
    assert "Rocket Capsule" not in strings
    web_title = (tmp_path / "run" / "project" / "web" / "index.html").read_text(encoding="utf-8")
    assert "<title>Tool Library</title>" in web_title
    from harness.branding import visible_rocket_capsule

    assert visible_rocket_capsule(tmp_path / "run" / "project") == []
    systems = [c[1] for c in fake.calls]
    assert systems[0] == CAPSULE_PREFIX
    assert systems[1] == CAPSULE_PREFIX
    assert systems[0] == systems[1]


def test_bare_mode_e2e(tmp_path: Path) -> None:
    def create_fn(dest: Path) -> None:
        dest.mkdir(parents=True)
        (dest / "lib").mkdir()
        (dest / "lib" / "main.dart").write_text("void main() {}\n", encoding="utf-8")
        (dest / "pubspec.yaml").write_text("name: bare_app\n", encoding="utf-8")
        (dest / "capsule.manifest.json").write_text(
            json.dumps({"protected_paths": ["pubspec.yaml"], "editable_paths": ["lib/**"]}),
            encoding="utf-8",
        )

    fake = FakePilot()
    fake.enqueue("spec", APP_SPEC)
    fake.enqueue("file_ops", BARE_OPS)
    session = _session(fake, tmp_path, "bare-1")
    result = run_build(
        "tool_library",
        session,
        mode="bare",
        run_dir=tmp_path / "run",
        capsule=CAPSULE,
        gate_fn=_pass_gate,
        create_fn=create_fn,
        build_web=False,
    )
    assert result["ok"]
    assert result["mode"] == "bare"
    assert "no scaffold" in fake.calls[0][1].lower() or "blank" in fake.calls[0][1].lower()
    assert (tmp_path / "run" / "project" / "lib" / "main.dart").read_text(encoding="utf-8") == BARE_MAIN


def test_guard_violation_is_fed_back_then_applied(tmp_path: Path) -> None:
    fake = FakePilot()
    fake.enqueue("spec", APP_SPEC)
    fake.enqueue("file_ops", PROTECTED_OPS, GOOD_OPS)
    session = _session(fake, tmp_path, "guard-1")
    result = run_build(
        "tool_library",
        session,
        mode="harness",
        run_dir=tmp_path / "run",
        capsule=CAPSULE,
        gate_fn=_pass_gate,
        build_web=False,
    )
    assert result["ok"]
    assert result["ops"]["guard_rounds"] >= 1
    assert any(v["code"] == "protected_path" for v in result["ops"]["violations"])
    assert "Guard violations" in fake.calls[2][2]
    core = tmp_path / "run" / "project" / "lib" / "core" / "auth" / "auth_service.dart"
    assert "void hack" not in core.read_text(encoding="utf-8")
    assert (tmp_path / "run" / "project" / "lib" / "app" / "features" / "notes" / "notes_screen.dart").is_file()


def test_build_writes_result_json_when_pilot_raises(tmp_path: Path) -> None:
    fake = FakePilot()
    fake.enqueue("spec", APP_SPEC)
    fake.enqueue("file_ops", RuntimeError("timeout: read timed out"))
    session = _session(fake, tmp_path, "err-1")
    result = run_build(
        "tool_library",
        session,
        mode="harness",
        run_dir=tmp_path / "run",
        capsule=CAPSULE,
        gate_fn=_pass_gate,
        build_web=False,
    )
    path = tmp_path / "run" / "result.json"
    assert path.is_file()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["ok"] is False
    assert "timeout" in (saved.get("error") or "")
    assert result["ok"] is False


def test_one_gate_repair_round(tmp_path: Path) -> None:
    n = {"i": 0}

    def flaky(project: Path) -> GateReport:
        n["i"] += 1
        if n["i"] == 1:
            return GateReport(
                project_dir=str(project),
                ok=False,
                steps=[StepResult("preflight", False, 1.0, "placeholder")],
                preflight=[
                    CheckResult("no_placeholders", CheckStatus.FAIL, "TODO found", "lib/app/features/notes/notes_screen.dart", 1)
                ],
            )
        return _pass_gate(project)

    fake = FakePilot()
    fake.enqueue("spec", APP_SPEC)
    fake.enqueue("file_ops", GOOD_OPS, GOOD_OPS)
    session = _session(fake, tmp_path, "repair-1")
    result = run_build(
        "tool_library",
        session,
        mode="harness",
        run_dir=tmp_path / "run",
        capsule=CAPSULE,
        gate_fn=flaky,
        build_web=False,
    )
    assert result["ok"]
    assert result["repair_rounds"] == 1
    assert n["i"] == 2
    assert any("Gate failed" in c[2] for c in fake.calls if c[0] == "file_ops")
