import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../auth/auth_service.dart';
import '../billing/billing_service.dart';
import '../kit/kit.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.auth, required this.billing});

  final AuthService auth;
  final BillingService billing;

  @override
  Widget build(BuildContext context) {
    return RocketScaffold(
      title: AppStrings.settingsTitle,
      showBottomNav: false,
      body: KitPage(
        children: [
          if (auth.isDemo || billing.isDemo)
            ListSection(
              children: [
                ListRow(
                  title: 'Demo mode',
                  emoji: '🧪',
                  subtitle: [
                    if (auth.isDemo) 'Firebase config not supplied; in-memory auth.',
                    if (billing.isDemo) 'RevenueCat key not supplied; mock billing.',
                  ].join(' '),
                ),
              ],
            ),
          ListSection(
            title: 'Legal',
            children: [
              ListRow(
                title: AppStrings.privacyLabel,
                emoji: '🔒',
                onTap: () => context.push('/privacy'),
              ),
              ListRow(
                title: AppStrings.termsLabel,
                emoji: '📄',
                onTap: () => context.push('/terms'),
              ),
            ],
          ),
          ListSection(
            title: 'Account',
            children: [
              ListRow(
                title: AppStrings.restoreLabel,
                emoji: '♻️',
                onTap: () => billing.restorePurchases(),
              ),
              ListRow(
                title: AppStrings.deleteAccountLabel,
                emoji: '🗑️',
                destructive: true,
                onTap: () async {
                  await auth.deleteAccount();
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Account deleted')),
                    );
                  }
                },
              ),
            ],
          ),
        ],
      ),
    );
  }
}
