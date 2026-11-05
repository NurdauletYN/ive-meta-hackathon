import 'package:flutter/material.dart';

import 'kit_extra.dart';
import 'kit_photos.dart';
import 'kit_widgets.dart';

/// Data the generated app fills in. Layout stays in these screens (v0/Lovable blocks).
class KitProduct {
  const KitProduct({
    required this.id,
    required this.title,
    this.subtitle,
    this.price,
    this.photo,
    this.badge,
    this.category,
    this.favorite = false,
    this.emoji,
  });

  final String id;
  final String title;
  final String? subtitle;
  final String? price;
  final String? photo;
  final String? badge;
  final String? category;
  final bool favorite;
  final String? emoji;

  String get resolvedPhoto => KitPhoto.resolve(photo: photo, title: title);
}

/// Shop / browse. Pass products; do not invent a layout.
class KitShopScreen extends StatelessWidget {
  const KitShopScreen({
    super.key,
    required this.heroTitle,
    this.heroSubtitle,
    this.heroPhoto,
    this.heroAction,
    this.onHeroAction,
    this.search,
    this.searchHint,
    this.filters = const [],
    this.selectedFilter,
    this.onFilter,
    this.items = const [],
    this.featured,
    this.onTap,
    this.onFavorite,
    this.sectionTitle = 'All',
  });

  final String heroTitle;
  final String? heroSubtitle;
  final String? heroPhoto;
  final String? heroAction;
  final VoidCallback? onHeroAction;
  final TextEditingController? search;
  final String? searchHint;
  final List<String> filters;
  final String? selectedFilter;
  final ValueChanged<String>? onFilter;
  final List<KitProduct> items;
  final List<KitProduct>? featured;
  final ValueChanged<KitProduct>? onTap;
  final ValueChanged<KitProduct>? onFavorite;
  final String sectionTitle;

  @override
  Widget build(BuildContext context) {
    final feature = featured ?? items.take(3).toList();
    return KitPage(
      children: [
        HeroHeader(
          title: heroTitle,
          subtitle: heroSubtitle,
          photo:
              heroPhoto ?? (items.isEmpty ? null : items.first.resolvedPhoto),
          actionLabel: heroAction,
          onAction: onHeroAction,
        ),
        if (feature.isNotEmpty) ...[
          const SectionHeader('Featured'),
          FeaturedRow(
            children: [
              for (final item in feature)
                FeaturedCard(
                  title: item.title,
                  subtitle: item.subtitle,
                  photo: item.resolvedPhoto,
                  badge: item.badge ?? item.category,
                  price: item.price,
                  onTap: onTap == null ? null : () => onTap!(item),
                ),
            ],
          ),
        ],
        if (search != null)
          AppTextField(
            controller: search!,
            hint: searchHint ?? 'Search',
            isSearch: true,
          ),
        if (filters.length > 1 && onFilter != null)
          ChipRow(
            labels: filters,
            selected: selectedFilter ?? filters.first,
            onSelected: onFilter!,
          ),
        SectionHeader(sectionTitle, actionLabel: '${items.length}'),
        if (items.isEmpty)
          const EmptyState(title: 'Nothing here yet', emoji: '📭')
        else
          ProductGrid(
            children: [
              for (final item in items)
                ProductCard(
                  title: item.title,
                  subtitle: item.subtitle,
                  price: item.price,
                  photo: item.resolvedPhoto,
                  badge: item.badge,
                  favorite: onFavorite == null ? null : item.favorite,
                  onFavorite: onFavorite == null
                      ? null
                      : () => onFavorite!(item),
                  onTap: onTap == null ? null : () => onTap!(item),
                ),
            ],
          ),
      ],
    );
  }
}

/// Product / item detail. Pass one [KitProduct]; do not invent a layout.
class KitDetailScreen extends StatelessWidget {
  const KitDetailScreen({
    super.key,
    required this.item,
    this.quantity = 1,
    this.onQuantity,
    this.primaryLabel,
    this.onPrimary,
    this.secondaryLabel,
    this.onSecondary,
    this.notes = const [],
  });

  final KitProduct item;
  final int quantity;
  final ValueChanged<int>? onQuantity;
  final String? primaryLabel;
  final VoidCallback? onPrimary;
  final String? secondaryLabel;
  final VoidCallback? onSecondary;
  final List<ListRow> notes;

  @override
  Widget build(BuildContext context) {
    return KitPage(
      children: [
        HeroHeader(
          title: item.title,
          subtitle: item.subtitle,
          photo: item.resolvedPhoto,
          actionLabel: item.price,
        ),
        if (onQuantity != null) ...[
          const SectionHeader('Quantity'),
          QuantityStepper(value: quantity, onChanged: onQuantity!, min: 1),
        ],
        if (item.price != null) PriceTag(text: item.price!),
        if (onPrimary != null)
          PrimaryButton(
            label: primaryLabel ?? 'Continue',
            onPressed: onPrimary,
          ),
        if (onSecondary != null)
          SecondaryButton(
            label: secondaryLabel ?? 'Back',
            onPressed: onSecondary,
          ),
        if (notes.isNotEmpty) ListSection(title: 'Details', children: notes),
      ],
    );
  }
}

/// Profile / summary.
class KitProfileScreen extends StatelessWidget {
  const KitProfileScreen({
    super.key,
    required this.title,
    this.subtitle,
    this.photo,
    this.emoji,
    this.stats = const [],
    this.rows = const [],
    this.actionLabel,
    this.onAction,
  });

  final String title;
  final String? subtitle;
  final String? photo;
  final String? emoji;
  final List<StatTile> stats;
  final List<ListRow> rows;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    return KitPage(
      children: [
        HeroHeader(
          title: title,
          subtitle: subtitle,
          photo: photo,
          emoji: photo == null ? emoji : null,
          actionLabel: actionLabel,
          onAction: onAction,
        ),
        if (stats.isNotEmpty) StatRow(children: stats),
        if (rows.isNotEmpty) ListSection(title: 'Account', children: rows),
      ],
    );
  }
}

/// Sign up / sign in. Controllers stay in the caller.
class KitAuthScreen extends StatelessWidget {
  const KitAuthScreen({
    super.key,
    required this.title,
    required this.subtitle,
    required this.email,
    required this.password,
    required this.primaryLabel,
    required this.onPrimary,
    required this.switchLabel,
    required this.onSwitch,
    this.photo,
    this.error,
  });

  final String title;
  final String subtitle;
  final TextEditingController email;
  final TextEditingController password;
  final String primaryLabel;
  final VoidCallback? onPrimary;
  final String switchLabel;
  final VoidCallback onSwitch;
  final String? photo;
  final String? error;

  @override
  Widget build(BuildContext context) {
    return KitPage(
      children: [
        HeroHeader(
          title: title,
          subtitle: subtitle,
          photo: photo ?? KitPhoto.path('watch'),
        ),
        AppTextField(
          controller: email,
          label: 'Email',
          hint: 'you@example.com',
          keyboardType: TextInputType.emailAddress,
        ),
        AppTextField(
          controller: password,
          label: 'Password',
          obscureText: true,
        ),
        if (error != null)
          Text(
            error!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        PrimaryButton(label: primaryLabel, onPressed: onPrimary),
        SecondaryButton(label: switchLabel, onPressed: onSwitch),
      ],
    );
  }
}
