import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/kit/kit_tokens.dart';

class AppTheme {
  AppTheme(this.data);

  final ThemeData data;

  static Future<AppTheme> load() async {
    final raw = await rootBundle.loadString('lib/app/design_tokens.json');
    return AppTheme(fromJson(jsonDecode(raw) as Map<String, dynamic>));
  }

  /// colors: primary, on_primary, surface, on_surface (required); accent, surface_alt (optional).
  /// A dark surface gives a dark theme.
  static ThemeData fromJson(Map<String, dynamic> json) {
    final colors = json['colors'] as Map<String, dynamic>;
    final primary = _color(colors['primary'] as String);
    final onPrimary = _color(colors['on_primary'] as String);
    final surface = _color(colors['surface'] as String);
    final onSurface = _color(colors['on_surface'] as String);
    final dark = ThemeData.estimateBrightnessForColor(surface) == Brightness.dark;
    final accent = colors['accent'] is String ? _color(colors['accent'] as String) : primary;
    final alt = colors['surface_alt'] is String
        ? _color(colors['surface_alt'] as String)
        : Color.alphaBlend(onSurface.withValues(alpha: 0.06), surface);
    final typography = json['typography'] as String? ?? 'default';
    final factor = switch (typography) {
      'compact' => 0.9,
      'expressive' => 1.12,
      _ => 1.0,
    };
    final kit = KitTokens.fromJson(json, typeFactor: factor);
    final base = dark ? ThemeData.dark() : ThemeData.light();
    return ThemeData(
      colorScheme: ColorScheme(
        brightness: dark ? Brightness.dark : Brightness.light,
        primary: primary,
        onPrimary: onPrimary,
        secondary: accent,
        onSecondary: onPrimary,
        tertiary: accent,
        onTertiary: onPrimary,
        error: dark ? Colors.red.shade300 : Colors.red.shade700,
        onError: dark ? Colors.black : Colors.white,
        surface: surface,
        onSurface: onSurface,
        surfaceContainerHighest: alt,
        surfaceContainerHigh: alt,
        surfaceContainer: alt,
        surfaceContainerLow: alt,
        outlineVariant: onSurface.withValues(alpha: 0.12),
      ),
      scaffoldBackgroundColor: surface,
      useMaterial3: true,
      fontFamily: 'KitSans',
      textTheme: base.textTheme.apply(
        fontFamily: 'KitSans',
        fontSizeFactor: factor,
        bodyColor: onSurface,
        displayColor: onSurface,
      ),
      splashFactory: InkSparkle.splashFactory,
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(shape: const StadiumBorder())),
      cardTheme: CardThemeData(
        elevation: 0,
        color: alt,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(kit.radii.lg)),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: surface,
        foregroundColor: onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      navigationBarTheme: NavigationBarThemeData(
        height: 68,
        elevation: 0,
        backgroundColor: alt,
        indicatorColor: primary.withValues(alpha: dark ? 0.28 : 0.16),
        labelTextStyle: WidgetStatePropertyAll(
          TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600, color: onSurface),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: alt,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(kit.radii.md), borderSide: BorderSide.none),
      ),
      extensions: [kit],
    );
  }

  static Color _color(String hex) {
    final value = hex.replaceFirst('#', '');
    return Color(int.parse('FF$value', radix: 16));
  }
}
