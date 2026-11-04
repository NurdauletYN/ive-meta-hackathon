import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'kit_tokens.dart';
import 'kit_widgets.dart';

/// Section title with an optional "See all" action.
class SectionHeader extends StatelessWidget {
  const SectionHeader(this.title, {super.key, this.actionLabel, this.onAction});

  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Expanded(
          child: Text(
            title,
            style: TextStyle(
              fontSize: tokens.typeScale.title,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.4,
              color: scheme.onSurface,
            ),
          ),
        ),
        if (actionLabel != null)
          GestureDetector(
            onTap: onAction,
            child: Text(
              actionLabel!,
              style: TextStyle(
                fontSize: tokens.typeScale.caption,
                fontWeight: FontWeight.w600,
                color: scheme.primary,
              ),
            ),
          ),
      ],
    );
  }
}

/// Big photo card with the title over a dark scrim. Use inside [FeaturedRow].
class FeaturedCard extends StatelessWidget {
  const FeaturedCard({
    super.key,
    required this.title,
    this.subtitle,
    this.photo,
    this.badge,
    this.price,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final String? photo;
  final String? badge;
  final String? price;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final radius = BorderRadius.circular(tokens.radii.lg + 4);
    return ClipRRect(
      borderRadius: radius,
      child: Stack(
        fit: StackFit.expand,
        children: [
          KitPhotoTile(title: title, photo: photo, size: null),
          const DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [Color(0x00000000), Color(0xB3000000)],
                stops: [0.42, 1],
              ),
            ),
          ),
          if (badge != null) Positioned(left: 12, top: 12, child: KitBadge(label: badge!, solid: true)),
          Positioned(
            left: 14,
            right: 14,
            bottom: 14,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: tokens.typeScale.title,
                          fontWeight: FontWeight.w700,
                          height: 1.1,
                          letterSpacing: -0.5,
                          color: Colors.white,
                        ),
                      ),
                      if (subtitle != null)
                        Padding(
                          padding: EdgeInsets.only(top: tokens.spacing.xs),
                          child: Text(
                            subtitle!,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: tokens.typeScale.caption,
                              color: Colors.white.withValues(alpha: 0.82),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                if (price != null)
                  Text(
                    price!,
                    style: TextStyle(
                      fontSize: tokens.typeScale.body,
                      fontWeight: FontWeight.w700,
                      color: Colors.white,
                    ),
                  ),
              ],
            ),
          ),
          Positioned.fill(
            child: Material(
              type: MaterialType.transparency,
              child: InkWell(onTap: onTap),
            ),
          ),
        ],
      ),
    );
  }
}

/// Horizontal carousel of [FeaturedCard]s.
class FeaturedRow extends StatelessWidget {
  const FeaturedRow({super.key, required this.children, this.height = 230, this.cardWidth = 250});

  final List<Widget> children;
  final double height;
  final double cardWidth;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return SizedBox(
      height: height,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: children.length,
        separatorBuilder: (_, __) => SizedBox(width: tokens.spacing.sm + 2),
        itemBuilder: (context, index) => SizedBox(width: cardWidth, child: children[index]),
      ),
    );
  }
}

/// Settings-style row: rounded icon tile, title, subtitle, trailing widget. Use instead of ListTile.
class ListRow extends StatelessWidget {
  const ListRow({
    super.key,
    required this.title,
    this.subtitle,
    this.emoji,
    this.icon,
    this.trailing,
    this.onTap,
    this.destructive = false,
  });

  final String title;
  final String? subtitle;
  final String? emoji;
  final IconData? icon;
  final Widget? trailing;
  final VoidCallback? onTap;
  final bool destructive;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final tone = destructive ? scheme.error : scheme.primary;
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: EdgeInsets.symmetric(horizontal: tokens.spacing.md, vertical: tokens.spacing.sm + 4),
        child: Row(
          children: [
            if (emoji != null || icon != null) ...[
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: tone.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(tokens.radii.md),
                ),
                child: emoji != null
                    ? Text(emoji!, style: const TextStyle(fontSize: 20, height: 1))
                    : Icon(icon, size: 20, color: tone),
              ),
              SizedBox(width: tokens.spacing.md),
            ],
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: tokens.typeScale.body,
                      fontWeight: FontWeight.w600,
                      color: destructive ? scheme.error : scheme.onSurface,
                    ),
                  ),
                  if (subtitle != null)
                    Padding(
                      padding: EdgeInsets.only(top: tokens.spacing.xs / 2),
                      child: Text(
                        subtitle!,
                        style: TextStyle(
                          fontSize: tokens.typeScale.caption,
                          height: 1.3,
                          color: scheme.onSurface.withValues(alpha: 0.6),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            if (trailing != null)
              trailing!
            else if (onTap != null)
              Icon(Icons.chevron_right, color: scheme.onSurface.withValues(alpha: 0.35)),
          ],
        ),
      ),
    );
  }
}

/// Rounded group of [ListRow]s with hairline dividers and an optional label.
class ListSection extends StatelessWidget {
  const ListSection({super.key, this.title, required this.children});

  final String? title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (title != null)
          Padding(
            padding: EdgeInsets.only(left: tokens.spacing.xs, bottom: tokens.spacing.sm),
            child: Text(
              title!.toUpperCase(),
              style: TextStyle(
                fontSize: tokens.typeScale.label,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.0,
                color: scheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
          ),
        Material(
          color: scheme.surfaceContainerHighest,
          clipBehavior: Clip.antiAlias,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(tokens.radii.lg)),
          child: Column(
            children: [
              for (var i = 0; i < children.length; i++) ...[
                if (i > 0)
                  Divider(
                    height: 1,
                    thickness: 1,
                    indent: tokens.spacing.md + 52,
                    color: scheme.onSurface.withValues(alpha: 0.07),
                  ),
                children[i],
              ],
            ],
          ),
        ),
      ],
    );
  }
}

/// Pill segmented control with a sliding thumb.
class SegmentedTabs extends StatelessWidget {
  const SegmentedTabs({
    super.key,
    required this.labels,
    required this.selected,
    required this.onSelected,
  });

  final List<String> labels;
  final String selected;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final index = labels.indexOf(selected).clamp(0, labels.length - 1);
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(tokens.radii.pill),
      ),
      child: Stack(
        children: [
          Positioned.fill(
            child: AnimatedAlign(
              duration: const Duration(milliseconds: 220),
              curve: Curves.easeOutCubic,
              alignment: Alignment(labels.length <= 1 ? 0 : -1 + 2 * index / (labels.length - 1), 0),
              child: FractionallySizedBox(
                widthFactor: 1 / labels.length,
                heightFactor: 1,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: scheme.primary,
                    borderRadius: BorderRadius.circular(tokens.radii.pill),
                  ),
                ),
              ),
            ),
          ),
          Row(
            children: [
              for (final label in labels)
                Expanded(
                  child: GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTap: () => onSelected(label),
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: tokens.spacing.sm + 2),
                      child: Center(
                        child: Text(
                          label,
                          style: TextStyle(
                            fontSize: tokens.typeScale.label + 1,
                            fontWeight: FontWeight.w700,
                            color: label == selected
                                ? scheme.onPrimary
                                : scheme.onSurface.withValues(alpha: 0.7),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Circular progress with a centered value label.
class ProgressRing extends StatelessWidget {
  const ProgressRing({super.key, required this.value, this.label, this.caption, this.size = 112});

  /// 0.0 to 1.0
  final double value;
  final String? label;
  final String? caption;
  final double size;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final clamped = value.clamp(0.0, 1.0);
    return SizedBox(
      width: size,
      height: size,
      child: TweenAnimationBuilder<double>(
        tween: Tween(begin: 0, end: clamped),
        duration: const Duration(milliseconds: 700),
        curve: Curves.easeOutCubic,
        builder: (context, v, _) => CustomPaint(
          painter: _RingPainter(
            value: v,
            track: scheme.onSurface.withValues(alpha: 0.08),
            color: scheme.primary,
            accent: scheme.tertiary,
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  label ?? '${(clamped * 100).round()}%',
                  style: TextStyle(
                    fontSize: tokens.typeScale.title,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.5,
                    color: scheme.onSurface,
                  ),
                ),
                if (caption != null)
                  Text(
                    caption!,
                    style: TextStyle(
                      fontSize: tokens.typeScale.label,
                      color: scheme.onSurface.withValues(alpha: 0.55),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RingPainter extends CustomPainter {
  _RingPainter({required this.value, required this.track, required this.color, required this.accent});

  final double value;
  final Color track;
  final Color color;
  final Color accent;

  @override
  void paint(Canvas canvas, Size size) {
    const stroke = 10.0;
    final rect = Offset.zero & size;
    final arc = rect.deflate(stroke / 2);
    final base = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..color = track;
    canvas.drawArc(arc, 0, math.pi * 2, false, base);
    final fg = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.round
      ..shader = SweepGradient(
        startAngle: -math.pi / 2,
        endAngle: math.pi * 1.5,
        colors: [color, accent, color],
        transform: const GradientRotation(-math.pi / 2),
      ).createShader(rect);
    canvas.drawArc(arc, -math.pi / 2, math.pi * 2 * value, false, fg);
  }

  @override
  bool shouldRepaint(_RingPainter old) => old.value != value || old.color != color;
}

/// Row of equal-width [StatTile]s.
class StatRow extends StatelessWidget {
  const StatRow({super.key, required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          for (var i = 0; i < children.length; i++) ...[
            if (i > 0) SizedBox(width: tokens.spacing.sm),
            Expanded(child: children[i]),
          ],
        ],
      ),
    );
  }
}
