import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

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
    final location = GoRouterState.of(context).uri.path;
    var current = 0;
    for (var i = 0; i < tabs.length; i++) {
      final path = tabs[i].path;
      final atHome = location == '/' || location == '/home';
      if (location == path || (atHome && path == KitNavigation.homePath)) {
        current = i;
      }
    }
    return Scaffold(
      backgroundColor: scheme.surface,
      appBar: AppBar(
        title: title == null
            ? null
            : Text(
                title!,
                style: TextStyle(
                  fontSize: tokens.typeScale.title,
                  fontWeight: FontWeight.w600,
                  color: scheme.onSurface,
                ),
              ),
        actions: actions,
        backgroundColor: scheme.surface,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
      ),
      body: body,
      floatingActionButton: floatingActionButton,
      bottomNavigationBar: showBottomNav && tabs.length >= 2
          ? NavigationBar(
              selectedIndex: current,
              onDestinationSelected: (index) {
                final path = tabs[index].path;
                context.go(path);
              },
              destinations: [
                for (final tab in tabs)
                  NavigationDestination(
                    icon: Text(tab.icon, style: TextStyle(fontSize: tokens.typeScale.title)),
                    label: tab.label,
                  ),
              ],
            )
          : null,
    );
  }
}

class HeroHeader extends StatelessWidget {
  const HeroHeader({
    super.key,
    required this.title,
    this.subtitle,
    this.emoji,
    this.icon,
  });

  final String title;
  final String? subtitle;
  final String? emoji;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(tokens.spacing.lg, tokens.spacing.lg, tokens.spacing.lg, tokens.spacing.md),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [scheme.primary, scheme.surface],
        ),
        borderRadius: BorderRadius.circular(tokens.radii.lg),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (emoji != null || icon != null)
            Padding(
              padding: EdgeInsets.only(bottom: tokens.spacing.sm),
              child: emoji != null
                  ? Text(emoji!, style: TextStyle(fontSize: tokens.typeScale.display))
                  : Icon(icon, color: scheme.onPrimary, size: tokens.typeScale.display),
            ),
          Text(
            title,
            style: TextStyle(
              fontSize: tokens.typeScale.display,
              fontWeight: FontWeight.w700,
              color: scheme.onPrimary,
            ),
          ),
          if (subtitle != null) ...[
            SizedBox(height: tokens.spacing.xs),
            Text(
              subtitle!,
              style: TextStyle(fontSize: tokens.typeScale.body, color: scheme.onPrimary.withValues(alpha: 0.9)),
            ),
          ],
        ],
      ),
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
      padding: EdgeInsets.only(top: tokens.spacing.md, bottom: tokens.spacing.sm),
      child: Text(
        text,
        style: TextStyle(
          fontSize: tokens.typeScale.title,
          fontWeight: FontWeight.w600,
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
    this.trailing,
    this.onTap,
  });

  final String title;
  final String? subtitle;
  final String? emoji;
  final IconData? icon;
  final Widget? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: EdgeInsets.only(bottom: tokens.spacing.sm),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(tokens.radii.md)),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: scheme.primary.withValues(alpha: 0.14),
          child: emoji != null
              ? Text(emoji!, style: TextStyle(fontSize: tokens.typeScale.title))
              : Icon(icon ?? Icons.circle, color: scheme.primary, size: tokens.typeScale.title),
        ),
        title: Text(
          title,
          style: TextStyle(fontSize: tokens.typeScale.body, fontWeight: FontWeight.w600, color: scheme.onSurface),
        ),
        subtitle: subtitle == null
            ? null
            : Text(
                subtitle!,
                style: TextStyle(fontSize: tokens.typeScale.caption, color: scheme.onSurface.withValues(alpha: 0.7)),
              ),
        trailing: trailing,
      ),
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
    return SizedBox(
      height: tokens.spacing.xl + tokens.spacing.sm,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: labels.length,
        separatorBuilder: (_, __) => SizedBox(width: tokens.spacing.sm),
        itemBuilder: (context, index) {
          final label = labels[index];
          final on = label == selected;
          return FilterChip(
            label: Text(label, style: TextStyle(fontSize: tokens.typeScale.label)),
            selected: on,
            onSelected: (_) => onSelected(label),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(tokens.radii.pill)),
          );
        },
      ),
    );
  }
}

class KitBadge extends StatelessWidget {
  const KitBadge({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Container(
      padding: EdgeInsets.symmetric(horizontal: tokens.spacing.sm, vertical: tokens.spacing.xs),
      decoration: BoxDecoration(
        color: scheme.primary.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(tokens.radii.pill),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: tokens.typeScale.label, fontWeight: FontWeight.w600, color: scheme.primary),
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
      style: TextStyle(fontSize: tokens.typeScale.body, fontWeight: FontWeight.w700, color: scheme.primary),
    );
  }
}

class StatTile extends StatelessWidget {
  const StatTile({super.key, required this.label, required this.value, this.emoji});

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
        color: scheme.surface,
        borderRadius: BorderRadius.circular(tokens.radii.md),
        border: Border.all(color: scheme.primary.withValues(alpha: 0.18)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (emoji != null) Text(emoji!, style: TextStyle(fontSize: tokens.typeScale.title)),
          SizedBox(height: tokens.spacing.xs),
          Text(
            value,
            style: TextStyle(fontSize: tokens.typeScale.title, fontWeight: FontWeight.w700, color: scheme.onSurface),
          ),
          Text(
            label,
            style: TextStyle(fontSize: tokens.typeScale.caption, color: scheme.onSurface.withValues(alpha: 0.7)),
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
            if (emoji != null) Text(emoji!, style: TextStyle(fontSize: tokens.typeScale.display * 1.4)),
            SizedBox(height: tokens.spacing.md),
            Text(
              title,
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: tokens.typeScale.title, fontWeight: FontWeight.w600, color: scheme.onSurface),
            ),
            if (body != null) ...[
              SizedBox(height: tokens.spacing.sm),
              Text(
                body!,
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: tokens.typeScale.body, color: scheme.onSurface.withValues(alpha: 0.7)),
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
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(tokens.radii.md)),
        ),
        child: Text(label, style: TextStyle(fontSize: tokens.typeScale.body, fontWeight: FontWeight.w600)),
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
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(tokens.radii.md)),
        ),
        child: Text(label, style: TextStyle(fontSize: tokens.typeScale.body)),
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
  });

  final TextEditingController controller;
  final String? label;
  final String? hint;
  final bool obscureText;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return TextField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      style: TextStyle(fontSize: tokens.typeScale.body),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(tokens.radii.md)),
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
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        IconButton(
          onPressed: value > min ? () => onChanged(value - 1) : null,
          icon: const Icon(Icons.remove_circle_outline),
        ),
        Text('$value', style: TextStyle(fontSize: tokens.typeScale.title, fontWeight: FontWeight.w600)),
        IconButton(
          onPressed: value < max ? () => onChanged(value + 1) : null,
          icon: const Icon(Icons.add_circle_outline),
        ),
      ],
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
      borderRadius: BorderRadius.vertical(top: Radius.circular(tokens.radii.lg)),
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
          children: [
            SectionTitle(title),
            child,
          ],
        ),
      );
    },
  );
}
