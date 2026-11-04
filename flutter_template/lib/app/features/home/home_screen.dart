import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/kit/kit.dart';
import '../../strings.dart';
import '../registry.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final extras = extraFeatureRoutes();
    final tokens = KitTokens.of(context);
    return RocketScaffold(
      title: AppStrings.homeTitle,
      body: ListView(
        padding: EdgeInsets.all(tokens.spacing.lg),
        children: [
          HeroHeader(
            title: AppStrings.appName,
            subtitle: 'Locked sign-in, onboarding, paywall and legal screens are already here.',
            emoji: '🚀',
          ),
          SizedBox(height: tokens.spacing.lg),
          PrimaryButton(
            label: AppStrings.paywallTitle,
            onPressed: () => context.push('/paywall'),
          ),
          SizedBox(height: tokens.spacing.sm),
          SecondaryButton(
            label: AppStrings.settingsTitle,
            onPressed: () => context.push('/settings'),
          ),
          if (extras.isNotEmpty) SectionTitle('More'),
          for (final feature in extras)
            ItemCard(
              emoji: feature.icon,
              title: feature.label,
              onTap: () => context.push(feature.path),
            ),
        ],
      ),
    );
  }
}
