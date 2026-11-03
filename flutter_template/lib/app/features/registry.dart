import 'package:flutter/material.dart';

/// Extra screens the Pilot may add. The first entry is the app home
/// (`/` in lib/core/router/app_router.dart). Keep this file's FeatureRoute class.
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

/// Return additional GoRouter routes. Default: none.
/// Example (do not leave example code here):
///   FeatureRoute(path: '/notes', label: 'Notes', builder: (c) => const NotesScreen())
List<FeatureRoute> extraFeatureRoutes() {
  return const [];
}
