"""Canned FakePilot scripts so the local UI can run offline."""

from __future__ import annotations

from .fake import FakePilot


def _write(path: str, content: str) -> dict:
    return {"op": "write", "path": path, "content": content, "find": None, "replace": None}


def _tokens(primary: str, *, radius: float, typography: str) -> dict:
    return {
        "colors": {
            "primary": primary,
            "on_primary": "#FFFFFF",
            "surface": "#F5F7FA",
            "on_surface": "#1A1A1A",
        },
        "contrast_pairs": [
            {"name": "body", "foreground": "#1A1A1A", "background": "#F5F7FA"},
            {"name": "cta", "foreground": "#FFFFFF", "background": primary},
        ],
        "corner_radius": radius,
        "typography": typography,
    }


def _direction(name: str, primary: str, *, radius: float, typography: str) -> dict:
    return {
        "name": name,
        "rationale": f"{name} direction for the gallery.",
        "tokens": _tokens(primary, radius=radius, typography=typography),
    }


DIRECTIONS = {
    "directions": [
        _direction("Harbor", "#1565C0", radius=8, typography="default"),
        _direction("Ember", "#C62828", radius=16, typography="compact"),
        _direction("Grove", "#2E7D32", radius=24, typography="expressive"),
    ]
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
  final controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Notes')),
      body: Column(children: [
        TextField(controller: controller, decoration: const InputDecoration(hintText: 'Add a tool')),
        FilledButton(
          onPressed: () {
            final text = controller.text.trim();
            if (text.isEmpty) return;
            setState(() { items.add(text); controller.clear(); });
          },
          child: const Text('Add'),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: items.length,
            itemBuilder: (c, i) => ListTile(
              title: Text(items[i]),
              trailing: IconButton(
                icon: const Icon(Icons.delete),
                onPressed: () => setState(() => items.removeAt(i)),
              ),
            ),
          ),
        ),
      ]),
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

FILE_OPS = {
    "operations": [
        _write("lib/app/features/notes/notes_screen.dart", NOTES_DART),
        _write("lib/app/features/registry.dart", REGISTRY_DART),
    ]
}

BARE_OPS = {
    "operations": [
        _write(
            "lib/main.dart",
            "import 'package:flutter/material.dart';\n\n"
            "void main() {\n"
            "  runApp(const MaterialApp(home: Text('Tool Library')));\n"
            "}\n",
        )
    ]
}


def canned_pilot() -> FakePilot:
    """Fresh queues for one design + one harness build + one bare build."""
    fake = FakePilot(cached_tokens=64)
    fake.enqueue("design", DIRECTIONS)
    fake.enqueue("spec", APP_SPEC, APP_SPEC)
    fake.enqueue("file_ops", FILE_OPS, FILE_OPS, BARE_OPS)
    return fake
