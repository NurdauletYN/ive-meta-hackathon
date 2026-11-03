import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class AppTheme {
  AppTheme(this.data);

  final ThemeData data;

  static Future<AppTheme> load() async {
    final raw = await rootBundle.loadString('lib/app/design_tokens.json');
    final json = jsonDecode(raw) as Map<String, dynamic>;
    final colors = json['colors'] as Map<String, dynamic>;
    final primary = _color(colors['primary'] as String);
    final onPrimary = _color(colors['on_primary'] as String);
    final surface = _color(colors['surface'] as String);
    final onSurface = _color(colors['on_surface'] as String);
    final radius = (json['corner_radius'] as num?)?.toDouble() ?? 12;
    final typography = json['typography'] as String? ?? 'default';
    final factor = switch (typography) {
      'compact' => 0.9,
      'expressive' => 1.12,
      _ => 1.0,
    };
    final shape = RoundedRectangleBorder(borderRadius: BorderRadius.circular(radius));
    return AppTheme(
      ThemeData(
        colorScheme: ColorScheme(
          brightness: Brightness.light,
          primary: primary,
          onPrimary: onPrimary,
          secondary: primary,
          onSecondary: onPrimary,
          error: Colors.red.shade700,
          onError: Colors.white,
          surface: surface,
          onSurface: onSurface,
        ),
        useMaterial3: true,
        textTheme: ThemeData.light().textTheme.apply(fontSizeFactor: factor),
        filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(shape: shape)),
        cardTheme: CardThemeData(shape: shape),
      ),
    );
  }

  static Color _color(String hex) {
    final value = hex.replaceFirst('#', '');
    return Color(int.parse('FF$value', radix: 16));
  }
}
