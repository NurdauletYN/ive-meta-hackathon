import 'package:flutter/material.dart';

class KitSpacing {
  const KitSpacing({
    required this.xs,
    required this.sm,
    required this.md,
    required this.lg,
    required this.xl,
  });

  final double xs;
  final double sm;
  final double md;
  final double lg;
  final double xl;

  static const fallback = KitSpacing(xs: 4, sm: 8, md: 16, lg: 24, xl: 32);

  factory KitSpacing.fromJson(Map<String, dynamic>? json) {
    if (json == null) return fallback;
    return KitSpacing(
      xs: _num(json['xs'], fallback.xs),
      sm: _num(json['sm'], fallback.sm),
      md: _num(json['md'], fallback.md),
      lg: _num(json['lg'], fallback.lg),
      xl: _num(json['xl'], fallback.xl),
    );
  }
}

class KitRadii {
  const KitRadii({
    required this.sm,
    required this.md,
    required this.lg,
    required this.pill,
  });

  final double sm;
  final double md;
  final double lg;
  final double pill;

  static const fallback = KitRadii(sm: 8, md: 12, lg: 20, pill: 999);

  factory KitRadii.fromJson(Map<String, dynamic>? json, {double? corner}) {
    if (json == null && corner == null) return fallback;
    final md = json == null ? (corner ?? fallback.md) : _num(json['md'], corner ?? fallback.md);
    return KitRadii(
      sm: json == null ? (corner ?? fallback.sm) * 0.66 : _num(json['sm'], fallback.sm),
      md: md,
      lg: json == null ? (corner ?? fallback.lg) : _num(json['lg'], fallback.lg),
      pill: json == null ? fallback.pill : _num(json['pill'], fallback.pill),
    );
  }
}

class KitTypeScale {
  const KitTypeScale({
    required this.display,
    required this.title,
    required this.body,
    required this.caption,
    required this.label,
  });

  final double display;
  final double title;
  final double body;
  final double caption;
  final double label;

  static const fallback = KitTypeScale(
    display: 28,
    title: 20,
    body: 16,
    caption: 13,
    label: 12,
  );

  KitTypeScale scaled(double factor) {
    return KitTypeScale(
      display: display * factor,
      title: title * factor,
      body: body * factor,
      caption: caption * factor,
      label: label * factor,
    );
  }

  factory KitTypeScale.fromJson(Map<String, dynamic>? json) {
    if (json == null) return fallback;
    return KitTypeScale(
      display: _num(json['display'], fallback.display),
      title: _num(json['title'], fallback.title),
      body: _num(json['body'], fallback.body),
      caption: _num(json['caption'], fallback.caption),
      label: _num(json['label'], fallback.label),
    );
  }
}

class KitTab {
  const KitTab({required this.path, required this.label, required this.icon});

  final String path;
  final String label;
  final String icon;
}

/// Filled by [AppRouter] from registered extra features. Avoids kit ↔ registry import cycles.
class KitNavigation {
  KitNavigation._();

  static List<KitTab> tabs = const [];
  static String homePath = '/home';

  static void bind(List<KitTab> next, {String? home}) {
    tabs = next.take(4).toList(growable: false);
    if (home != null && home.isNotEmpty) homePath = home;
  }
}

class KitTokens extends ThemeExtension<KitTokens> {
  const KitTokens({
    required this.spacing,
    required this.radii,
    required this.typeScale,
  });

  final KitSpacing spacing;
  final KitRadii radii;
  final KitTypeScale typeScale;

  static KitTokens fallback() => const KitTokens(
        spacing: KitSpacing.fallback,
        radii: KitRadii.fallback,
        typeScale: KitTypeScale.fallback,
      );

  static KitTokens of(BuildContext context) {
    return Theme.of(context).extension<KitTokens>() ?? fallback();
  }

  factory KitTokens.fromJson(Map<String, dynamic> json, {double typeFactor = 1}) {
    final corner = (json['corner_radius'] as num?)?.toDouble();
    return KitTokens(
      spacing: KitSpacing.fromJson(json['spacing'] as Map<String, dynamic>?),
      radii: KitRadii.fromJson(json['radii'] as Map<String, dynamic>?, corner: corner),
      typeScale: KitTypeScale.fromJson(json['type_scale'] as Map<String, dynamic>?).scaled(typeFactor),
    );
  }

  @override
  KitTokens copyWith({
    KitSpacing? spacing,
    KitRadii? radii,
    KitTypeScale? typeScale,
  }) {
    return KitTokens(
      spacing: spacing ?? this.spacing,
      radii: radii ?? this.radii,
      typeScale: typeScale ?? this.typeScale,
    );
  }

  @override
  KitTokens lerp(ThemeExtension<KitTokens>? other, double t) {
    if (other is! KitTokens) return this;
    return t < 0.5 ? this : other;
  }
}

double _num(Object? value, double fallback) {
  if (value is num) return value.toDouble();
  return fallback;
}
