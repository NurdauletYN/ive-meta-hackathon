import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'kit_extra.dart';
import 'kit_photos.dart';
import 'kit_tokens.dart';

class RocketScaffold extends StatelessWidget {
  const RocketScaffold({
    super.key,
    required this.body,
    this.title,
    this.actions,
    this.floatingActionButton,
    this.showBottomNav = true,
  });

  final Widget body;
  final String? title;
  final List<Widget>? actions;
  final Widget? floatingActionButton;
  final bool showBottomNav;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final tabs = KitNavigation.tabs;
    final location = GoRouter.maybeOf(context) == null
        ? ''
        : GoRouterState.of(context).uri.path;
    var current = 0;
    for (var i = 0; i < tabs.length; i++) {
      final path = tabs[i].path;
      final atHome = location == '/' || location == '/home';
      if (location == path || (atHome && path == KitNavigation.homePath)) {
        current = i;
      }
    }
    final showBar = title != null || (actions != null && actions!.isNotEmpty);
    final showTabs = showBottomNav && tabs.length >= 2;
    final padded = Padding(
      padding: EdgeInsets.fromLTRB(
        tokens.spacing.sm,
        showBar ? 0 : tokens.spacing.sm,
        tokens.spacing.sm,
        showTabs ? tokens.spacing.sm : tokens.spacing.md,
      ),
      child: showBar
          ? Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: EdgeInsets.fromLTRB(
                    tokens.spacing.sm,
                    tokens.spacing.xs,
                    tokens.spacing.sm,
                    tokens.spacing.sm,
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: title == null
                            ? const SizedBox.shrink()
                            : Text(
                                title!,
                                style: TextStyle(
                                  fontSize: tokens.typeScale.title + 4,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: -0.7,
                                  color: scheme.onSurface,
                                ),
                              ),
                      ),
                      ...?actions,
                    ],
                  ),
                ),
                Expanded(child: body),
              ],
            )
          : body,
    );
    return Scaffold(
      backgroundColor: scheme.surface,
      extendBody: showTabs,
      body: SafeArea(bottom: !showTabs, child: padded),
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: showTabs
          ? Padding(
              padding: EdgeInsets.fromLTRB(
                tokens.spacing.md,
                0,
                tokens.spacing.md,
                tokens.spacing.sm,
              ),
              child: Material(
                color: scheme.surfaceContainerHighest,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(tokens.radii.pill),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(4),
                  child: Row(
                    children: [
                      for (var i = 0; i < tabs.length; i++)
                        Expanded(
                          child: _TabButton(
                            tab: tabs[i],
                            selected: i == current,
                            onTap: () => context.go(tabs[i].path),
                            tokens: tokens,
                            scheme: scheme,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            )
          : null,
    );
  }
}

class _TabButton extends StatelessWidget {
  const _TabButton({
    required this.tab,
    required this.selected,
    required this.onTap,
    required this.tokens,
    required this.scheme,
  });

  final KitTab tab;
  final bool selected;
  final VoidCallback onTap;
  final KitTokens tokens;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOutCubic,
        padding: EdgeInsets.symmetric(vertical: tokens.spacing.sm + 2),
        decoration: BoxDecoration(
          color: selected ? scheme.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(tokens.radii.pill),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              tab.icon,
              style: TextStyle(
                fontSize: 16,
                height: 1,
                color: selected ? scheme.onPrimary : scheme.onSurface,
              ),
            ),
            SizedBox(height: tokens.spacing.xs),
            Text(
              tab.label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: tokens.typeScale.label,
                fontWeight: FontWeight.w700,
                color: selected
                    ? scheme.onPrimary
                    : scheme.onSurface.withValues(alpha: 0.62),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class KitPage extends StatelessWidget {
  const KitPage({super.key, required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return ListView.separated(
      padding: EdgeInsets.fromLTRB(
        tokens.spacing.md + 4,
        tokens.spacing.md,
        tokens.spacing.md + 4,
        tokens.spacing.xl + 12,
      ),
      itemCount: children.length,
      separatorBuilder: (context, index) {
        final current = children[index];
        final next = index + 1 < children.length ? children[index + 1] : null;
        final loose =
            current is HeroHeader ||
            current is ChipRow ||
            current is AppTextField ||
            current is SectionTitle ||
            current is SectionHeader ||
            current is SegmentedTabs ||
            next is SectionTitle ||
            next is SectionHeader ||
            next is HeroHeader;
        return SizedBox(height: loose ? tokens.spacing.md : tokens.spacing.sm);
      },
      itemBuilder: (context, index) =>
          Reveal(index: index, child: children[index]),
    );
  }
}

/// Fade and rise-in used by [KitPage] so screens feel alive on first paint.
class Reveal extends StatelessWidget {
  const Reveal({super.key, required this.child, this.index = 0});

  final Widget child;
  final int index;

  @override
  Widget build(BuildContext context) {
    final delay = (index > 6 ? 6 : index) * 55;
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0, end: 1),
      duration: Duration(milliseconds: 380 + delay),
      curve: Curves.easeOutCubic,
      builder: (context, t, child) => Opacity(
        opacity: t,
        child: Transform.translate(
          offset: Offset(0, (1 - t) * 18),
          child: child,
        ),
      ),
      child: child,
    );
  }
}

/// Gradient banner with soft shapes. Optional photo and call-to-action pill.
class HeroHeader extends StatelessWidget {
  const HeroHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.emoji,
    this.icon,
    this.photo,
    this.actionLabel,
    this.onAction,
  });

  final String title;
  final String? subtitle;
  final String? emoji;
  final IconData? icon;
  final String? photo;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final end =
        Color.lerp(scheme.primary, scheme.tertiary, 0.4) ?? scheme.primary;
    final fg = scheme.onPrimary;
    final radius = BorderRadius.circular(tokens.radii.lg + 6);
    final text = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (emoji != null || icon != null)
          Padding(
            padding: EdgeInsets.only(bottom: tokens.spacing.sm),
            child: emoji != null
                ? Text(
                    emoji!,
                    style: TextStyle(fontSize: tokens.typeScale.display),
                  )
                : Icon(icon, color: fg, size: tokens.typeScale.display),
          ),
        Text(
          title,
          style: TextStyle(
            fontSize: tokens.typeScale.display,
            fontWeight: FontWeight.w700,
            height: 1.08,
            letterSpacing: -0.9,
            color: fg,
          ),
        ),
        if (subtitle != null) ...[
          SizedBox(height: tokens.spacing.sm),
          Text(
            subtitle!,
            style: TextStyle(
              fontSize: tokens.typeScale.body,
              height: 1.35,
              color: fg.withValues(alpha: 0.82),
            ),
          ),
        ],
        if (actionLabel != null) ...[
          SizedBox(height: tokens.spacing.md),
          Material(
            color: fg,
            shape: const StadiumBorder(),
            child: InkWell(
              onTap: onAction,
              customBorder: const StadiumBorder(),
              child: Padding(
                padding: EdgeInsets.symmetric(
                  horizontal: tokens.spacing.lg,
                  vertical: tokens.spacing.sm + 2,
                ),
                child: Text(
                  actionLabel!,
                  style: TextStyle(
                    fontSize: tokens.typeScale.label + 1,
                    fontWeight: FontWeight.w700,
                    color: scheme.primary,
                  ),
                ),
              ),
            ),
          ),
        ],
      ],
    );
    return ClipRRect(
      borderRadius: radius,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [scheme.primary, end],
          ),
        ),
        child: Stack(
          children: [
            Positioned(
              right: -40,
              top: -50,
              child: _Blob(size: 170, color: fg.withValues(alpha: 0.10)),
            ),
            Positioned(
              left: -30,
              bottom: -60,
              child: _Blob(
                size: 150,
                color: scheme.tertiary.withValues(alpha: 0.22),
              ),
            ),
            Padding(
              padding: EdgeInsets.all(tokens.spacing.lg),
              child: photo == null
                  ? SizedBox(width: double.infinity, child: text)
                  : Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        Expanded(flex: 5, child: text),
                        SizedBox(width: tokens.spacing.md),
                        Expanded(
                          flex: 4,
                          child: AspectRatio(
                            aspectRatio: 1,
                            child: DecoratedBox(
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(
                                  tokens.radii.lg,
                                ),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withValues(alpha: 0.28),
                                    blurRadius: 24,
                                    offset: const Offset(0, 12),
                                  ),
                                ],
                              ),
                              child: KitPhotoTile(
                                title: title,
                                photo: photo,
                                size: null,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Blob extends StatelessWidget {
  const _Blob({required this.size, required this.color});

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return Padding(
      padding: EdgeInsets.only(
        top: tokens.spacing.xs,
        bottom: tokens.spacing.xs,
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: tokens.typeScale.title,
          fontWeight: FontWeight.w600,
          letterSpacing: -0.3,
          color: Theme.of(context).colorScheme.onSurface,
        ),
      ),
    );
  }
}

class ItemCard extends StatelessWidget {
  const ItemCard({
    super.key,
    required this.title,
    this.subtitle,
    this.emoji,
    this.icon,
    this.photo,
    this.price,
    this.trailing,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final String? emoji;
  final IconData? icon;
  final String? photo;
  final String? price;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final radius = BorderRadius.circular(tokens.radii.lg);
    return Material(
      color: scheme.surfaceContainerHighest,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: radius),
      child: InkWell(
        onTap: onTap,
        borderRadius: radius,
        child: Padding(
          padding: EdgeInsets.all(tokens.spacing.sm + 2),
          child: Row(
            children: [
              KitPhotoTile(
                title: title,
                photo: photo,
                emoji: emoji,
                icon: icon,
                size: 88,
              ),
              SizedBox(width: tokens.spacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        fontSize: tokens.typeScale.body,
                        fontWeight: FontWeight.w600,
                        letterSpacing: -0.2,
                        color: scheme.onSurface,
                      ),
                    ),
                    if (subtitle != null) ...[
                      SizedBox(height: tokens.spacing.xs),
                      Text(
                        subtitle!,
                        style: TextStyle(
                          fontSize: tokens.typeScale.caption,
                          height: 1.3,
                          color: scheme.onSurface.withValues(alpha: 0.58),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (price != null) ...[
                SizedBox(width: tokens.spacing.sm),
                PriceTag(text: price!),
              ],
              if (trailing != null) ...[
                SizedBox(width: tokens.spacing.sm),
                trailing!,
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class KitPhotoTile extends StatelessWidget {
  const KitPhotoTile({
    super.key,
    required this.title,
    this.photo,
    this.emoji,
    this.icon,
    this.size = 88,
  });

  final String title;
  final String? photo;
  final String? emoji;
  final IconData? icon;
  final double? size;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final path = KitPhoto.resolve(photo: photo, title: title);
    final side = size ?? 88;
    Widget fallback(_, __, ___) {
      final raw = emoji ?? '';
      final letter =
          raw.isEmpty ||
          (raw.characters.first.length == 1 && raw.codeUnitAt(0) < 128);
      return ColoredBox(
        color: scheme.primary.withValues(alpha: 0.12),
        child: Center(
          child: letter
              ? Icon(
                  icon ?? Icons.image_outlined,
                  color: scheme.primary,
                  size: side * 0.36,
                )
              : Text(raw, style: TextStyle(fontSize: side * 0.36, height: 1)),
        ),
      );
    }

    final image = Image.asset(path, fit: BoxFit.cover, errorBuilder: fallback);
    final clipped = ClipRRect(
      borderRadius: BorderRadius.circular(tokens.radii.md),
      child: size == null ? SizedBox.expand(child: image) : image,
    );
    if (size == null) return clipped;
    return SizedBox(width: side, height: side, child: clipped);
  }
}

class ProductCard extends StatelessWidget {
  const ProductCard({
    super.key,
    required this.title,
    this.subtitle,
    this.price,
    this.photo,
    this.emoji,
    this.badge,
    this.favorite,
    this.onFavorite,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final String? price;
  final String? photo;
  final String? emoji;
  final String? badge;
  final bool? favorite;
  final VoidCallback? onFavorite;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final radius = BorderRadius.circular(tokens.radii.lg);
    return Material(
      color: scheme.surfaceContainerHighest,
      shape: RoundedRectangleBorder(borderRadius: radius),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Padding(
                padding: EdgeInsets.all(tokens.spacing.sm - 2),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    KitPhotoTile(
                      title: title,
                      photo: photo,
                      emoji: emoji,
                      size: null,
                    ),
                    if (badge != null)
                      Positioned(
                        left: 8,
                        top: 8,
                        child: KitBadge(label: badge!, solid: true),
                      ),
                    if (favorite != null || onFavorite != null)
                      Positioned(
                        right: 6,
                        top: 6,
                        child: Material(
                          color: scheme.surface.withValues(alpha: 0.92),
                          shape: const CircleBorder(),
                          child: InkWell(
                            customBorder: const CircleBorder(),
                            onTap: onFavorite,
                            child: SizedBox(
                              width: 32,
                              height: 32,
                              child: Icon(
                                favorite == true
                                    ? Icons.favorite
                                    : Icons.favorite_border,
                                size: 18,
                                color: favorite == true
                                    ? scheme.tertiary
                                    : scheme.onSurface,
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(
                tokens.spacing.sm + 2,
                tokens.spacing.xs,
                tokens.spacing.sm + 2,
                tokens.spacing.md,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: tokens.typeScale.body,
                      fontWeight: FontWeight.w600,
                      letterSpacing: -0.2,
                      color: scheme.onSurface,
                    ),
                  ),
                  if (subtitle != null)
                    Text(
                      subtitle!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: tokens.typeScale.caption,
                        color: scheme.onSurface.withValues(alpha: 0.55),
                      ),
                    ),
                  if (price != null) ...[
                    SizedBox(height: tokens.spacing.xs),
                    PriceTag(text: price!),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ProductGrid extends StatelessWidget {
  const ProductGrid({super.key, required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: tokens.spacing.sm,
      crossAxisSpacing: tokens.spacing.sm,
      childAspectRatio: 0.74,
      children: children,
    );
  }
}

class ChipRow extends StatelessWidget {
  const ChipRow({
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
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (var i = 0; i < labels.length; i++) ...[
            if (i > 0) SizedBox(width: tokens.spacing.sm),
            _FilterPill(
              label: labels[i],
              selected: labels[i] == selected,
              onTap: () => onSelected(labels[i]),
              tokens: tokens,
              scheme: scheme,
            ),
          ],
        ],
      ),
    );
  }
}

class _FilterPill extends StatelessWidget {
  const _FilterPill({
    required this.label,
    required this.selected,
    required this.onTap,
    required this.tokens,
    required this.scheme,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final KitTokens tokens;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? scheme.primary : scheme.surfaceContainerHighest,
      shape: const StadiumBorder(),
      child: InkWell(
        onTap: onTap,
        customBorder: const StadiumBorder(),
        child: Padding(
          padding: EdgeInsets.symmetric(
            horizontal: tokens.spacing.md,
            vertical: tokens.spacing.sm,
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: tokens.typeScale.label,
              fontWeight: FontWeight.w600,
              color: selected
                  ? scheme.onPrimary
                  : scheme.onSurface.withValues(alpha: 0.78),
            ),
          ),
        ),
      ),
    );
  }
}

class KitBadge extends StatelessWidget {
  const KitBadge({super.key, required this.label, this.solid = false});

  final String label;
  final bool solid;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: tokens.spacing.sm + 2,
        vertical: tokens.spacing.xs,
      ),
      decoration: BoxDecoration(
        color: solid ? scheme.primary : scheme.primary.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(tokens.radii.pill),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: tokens.typeScale.label,
          fontWeight: FontWeight.w700,
          color: solid ? scheme.onPrimary : scheme.primary,
        ),
      ),
    );
  }
}

class PriceTag extends StatelessWidget {
  const PriceTag({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Text(
      text,
      style: TextStyle(
        fontSize: tokens.typeScale.body,
        fontWeight: FontWeight.w700,
        letterSpacing: -0.3,
        color: scheme.primary,
      ),
    );
  }
}

class StatTile extends StatelessWidget {
  const StatTile({
    super.key,
    required this.label,
    required this.value,
    this.emoji,
  });

  final String label;
  final String value;
  final String? emoji;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(tokens.spacing.md),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(tokens.radii.lg),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (emoji != null)
            Text(emoji!, style: TextStyle(fontSize: tokens.typeScale.title)),
          SizedBox(height: tokens.spacing.xs),
          Text(
            value,
            style: TextStyle(
              fontSize: tokens.typeScale.title,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.4,
              color: scheme.onSurface,
            ),
          ),
          Text(
            label,
            style: TextStyle(
              fontSize: tokens.typeScale.caption,
              color: scheme.onSurface.withValues(alpha: 0.58),
            ),
          ),
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.title, this.body, this.emoji});

  final String title;
  final String? body;
  final String? emoji;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: EdgeInsets.all(tokens.spacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (emoji != null)
              Text(
                emoji!,
                style: TextStyle(fontSize: tokens.typeScale.display * 1.4),
              ),
            SizedBox(height: tokens.spacing.md),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: tokens.typeScale.title,
                fontWeight: FontWeight.w600,
                color: scheme.onSurface,
              ),
            ),
            if (body != null) ...[
              SizedBox(height: tokens.spacing.sm),
              Text(
                body!,
                textAlign: TextAlign.center,
                style: TextStyle(
                  fontSize: tokens.typeScale.body,
                  color: scheme.onSurface.withValues(alpha: 0.62),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({super.key, required this.label, this.onPressed});

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return SizedBox(
      width: double.infinity,
      child: FilledButton(
        onPressed: onPressed,
        style: FilledButton.styleFrom(
          padding: EdgeInsets.symmetric(vertical: tokens.spacing.md),
          shape: const StadiumBorder(),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: tokens.typeScale.body,
            fontWeight: FontWeight.w700,
            letterSpacing: -0.1,
          ),
        ),
      ),
    );
  }
}

class SecondaryButton extends StatelessWidget {
  const SecondaryButton({super.key, required this.label, this.onPressed});

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        onPressed: onPressed,
        style: OutlinedButton.styleFrom(
          padding: EdgeInsets.symmetric(vertical: tokens.spacing.md),
          shape: const StadiumBorder(),
          side: BorderSide(
            color: Theme.of(
              context,
            ).colorScheme.onSurface.withValues(alpha: 0.18),
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: tokens.typeScale.body,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}

class AppTextField extends StatelessWidget {
  const AppTextField({
    super.key,
    required this.controller,
    this.label,
    this.hint,
    this.obscureText = false,
    this.keyboardType,
    this.isSearch = false,
  });

  final TextEditingController controller;
  final String? label;
  final String? hint;
  final bool obscureText;
  final TextInputType? keyboardType;
  final bool isSearch;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    final radius = BorderRadius.circular(
      isSearch ? tokens.radii.pill : tokens.radii.md,
    );
    return TextField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      style: TextStyle(fontSize: tokens.typeScale.body),
      decoration: InputDecoration(
        labelText: isSearch ? null : label,
        hintText: hint ?? (isSearch ? 'Search' : null),
        prefixIcon: isSearch
            ? Icon(
                Icons.search,
                color: scheme.onSurface.withValues(alpha: 0.45),
              )
            : null,
        filled: true,
        fillColor: scheme.surfaceContainerHighest,
        contentPadding: EdgeInsets.symmetric(
          horizontal: tokens.spacing.md,
          vertical: tokens.spacing.md,
        ),
        border: OutlineInputBorder(
          borderRadius: radius,
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: radius,
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: radius,
          borderSide: BorderSide(color: scheme.primary.withValues(alpha: 0.45)),
        ),
      ),
    );
  }
}

class QuantityStepper extends StatelessWidget {
  const QuantityStepper({
    super.key,
    required this.value,
    required this.onChanged,
    this.min = 0,
    this.max = 99,
  });

  final int value;
  final ValueChanged<int> onChanged;
  final int min;
  final int max;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        _StepButton(
          icon: Icons.remove,
          enabled: value > min,
          onTap: () => onChanged(value - 1),
          tokens: tokens,
          scheme: scheme,
        ),
        Padding(
          padding: EdgeInsets.symmetric(horizontal: tokens.spacing.sm),
          child: Text(
            '$value',
            style: TextStyle(
              fontSize: tokens.typeScale.title,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
        _StepButton(
          icon: Icons.add,
          enabled: value < max,
          onTap: () => onChanged(value + 1),
          tokens: tokens,
          scheme: scheme,
        ),
      ],
    );
  }
}

class _StepButton extends StatelessWidget {
  const _StepButton({
    required this.icon,
    required this.enabled,
    required this.onTap,
    required this.tokens,
    required this.scheme,
  });

  final IconData icon;
  final bool enabled;
  final VoidCallback onTap;
  final KitTokens tokens;
  final ColorScheme scheme;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: scheme.primary.withValues(alpha: enabled ? 0.12 : 0.05),
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: enabled ? onTap : null,
        child: SizedBox(
          width: 32,
          height: 32,
          child: Icon(
            icon,
            size: 16,
            color: enabled
                ? scheme.primary
                : scheme.onSurface.withValues(alpha: 0.28),
          ),
        ),
      ),
    );
  }
}

class CartBar extends StatelessWidget {
  const CartBar({super.key, required this.labels, this.onRemove});

  final List<String> labels;
  final ValueChanged<String>? onRemove;

  @override
  Widget build(BuildContext context) {
    if (labels.isEmpty) return const SizedBox.shrink();
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          for (var i = 0; i < labels.length; i++) ...[
            if (i > 0) SizedBox(width: tokens.spacing.sm),
            InputChip(
              label: Text(
                labels[i],
                style: TextStyle(fontSize: tokens.typeScale.label),
              ),
              onDeleted: onRemove == null ? null : () => onRemove!(labels[i]),
              backgroundColor: scheme.surfaceContainerHighest,
              side: BorderSide.none,
              shape: const StadiumBorder(),
            ),
          ],
        ],
      ),
    );
  }
}

Future<T?> showKitFormSheet<T>(
  BuildContext context, {
  required String title,
  required Widget child,
}) {
  final tokens = KitTokens.of(context);
  return showModalBottomSheet<T>(
    context: context,
    isScrollControlled: true,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(
        top: Radius.circular(tokens.radii.lg),
      ),
    ),
    builder: (sheetContext) {
      return Padding(
        padding: EdgeInsets.fromLTRB(
          tokens.spacing.lg,
          tokens.spacing.md,
          tokens.spacing.lg,
          tokens.spacing.lg + MediaQuery.viewInsetsOf(sheetContext).bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [SectionTitle(title), child],
        ),
      );
    },
  );
}
