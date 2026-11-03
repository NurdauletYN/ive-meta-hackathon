import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../billing/billing_service.dart';
import 'subscription_disclosure.dart';

class PaywallScreen extends StatelessWidget {
  const PaywallScreen({super.key, required this.billing});

  final BillingService billing;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.paywallTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SubscriptionDisclosure(),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => billing.purchase('rocket_plus_monthly'),
              child: const Text(AppStrings.subscribeLabel),
            ),
            TextButton(onPressed: () => context.push('/privacy'), child: const Text(AppStrings.privacyLabel)),
            TextButton(onPressed: () => context.push('/'), child: const Text(AppStrings.termsLabel)),
          ],
        ),
      ),
    );
  }
}
