import 'package:flutter/material.dart';

/// Extra screens the Pilot may add. The first entry is the app home
/// (`/` and `/home` in lib/core/router/app_router.dart). Keep this file's FeatureRoute class.
/// Mark up to 4 routes with `tab: true` and an emoji `icon` for bottom navigation.
class FeatureRoute {
  const FeatureRoute({
    required this.path,
    required this.label,
    required this.builder,
    this.icon = '•',
    this.tab = false,
  });

  final String path;
  final String label;
  final WidgetBuilder builder;
  final String icon;
  final bool tab;
}

/// Return additional GoRouter routes. Default: none.
/// Example (do not leave example code here):
///   FeatureRoute(path: '/notes', label: 'Notes', icon: '📝', tab: true, builder: (c) => const NotesScreen())
List<FeatureRoute> extraFeatureRoutes() {
  return const [];
}
