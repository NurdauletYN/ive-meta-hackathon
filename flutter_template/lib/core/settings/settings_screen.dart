import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../auth/auth_service.dart';
import '../billing/billing_service.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key, required this.auth, required this.billing});

  final AuthService auth;
  final BillingService billing;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.settingsTitle)),
      body: ListView(
        children: [
          if (auth.isDemo)
            const ListTile(
              title: Text('demo mode'),
              subtitle: Text('Firebase config not supplied; in-memory auth.'),
            ),
          ListTile(
            title: const Text(AppStrings.privacyLabel),
            onTap: () => context.push('/privacy'),
          ),
          ListTile(
            title: const Text(AppStrings.termsLabel),
            onTap: () => context.push('/terms'),
          ),
          ListTile(
            title: const Text(AppStrings.restoreLabel),
            onTap: () => billing.restorePurchases(),
          ),
          ListTile(
            title: const Text(AppStrings.deleteAccountLabel),
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
    );
  }
}
