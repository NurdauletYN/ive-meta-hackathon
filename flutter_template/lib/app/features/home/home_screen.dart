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
    return RocketScaffold(
      body: KitPage(
        children: [
          HeroHeader(
            title: AppStrings.appName,
            subtitle:
                'Sign in, onboarding, paywall and legal screens are already in the capsule.',
            photo: KitPhoto.bag,
            actionLabel: AppStrings.paywallTitle,
            onAction: () => context.push('/paywall'),
          ),
          StatRow(
            children: const [
              StatTile(label: 'Screens', value: 'Ready', emoji: '📱'),
              StatTile(label: 'Store', value: 'Gate', emoji: '✅'),
            ],
          ),
          ListSection(
            title: 'App',
            children: [
              ListRow(
                title: AppStrings.paywallTitle,
                subtitle: 'Restore and subscribe',
                emoji: '✨',
                onTap: () => context.push('/paywall'),
              ),
              ListRow(
                title: AppStrings.settingsTitle,
                subtitle: 'Privacy, terms, account',
                emoji: '⚙️',
                onTap: () => context.push('/settings'),
              ),
              for (final feature in extras)
                ListRow(
                  title: feature.label,
                  emoji: feature.icon,
                  onTap: () => context.push(feature.path),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
