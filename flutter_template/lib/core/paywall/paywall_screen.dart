import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../billing/billing_service.dart';
import '../billing/offering_product.dart';
import 'subscription_disclosure.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key, required this.billing});

  final BillingService billing;

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late final Future<List<OfferingProduct>> _offerings = widget.billing.offerings();

  Future<void> _subscribe([String? productId]) async {
    var id = productId;
    if (id == null) {
      final items = await widget.billing.offerings();
      id = items.isNotEmpty ? items.first.id : 'rocket_plus_monthly';
    }
    await widget.billing.purchase(id);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text(AppStrings.paywallTitle)),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: FutureBuilder<List<OfferingProduct>>(
          future: _offerings,
          builder: (context, snapshot) {
            final items = snapshot.data ?? const <OfferingProduct>[];
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const SubscriptionDisclosure(),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: () => _subscribe(items.isNotEmpty ? items.first.id : null),
                  child: const Text(AppStrings.subscribeLabel),
                ),
                for (final product in items)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: OutlinedButton(
                      onPressed: () => _subscribe(product.id),
                      child: Text('${product.title} · ${product.priceLabel}'),
                    ),
                  ),
                TextButton(
                  onPressed: () => widget.billing.restorePurchases(),
                  child: const Text(AppStrings.restoreLabel),
                ),
                TextButton(onPressed: () => context.push('/privacy'), child: const Text(AppStrings.privacyLabel)),
                TextButton(onPressed: () => context.push('/terms'), child: const Text(AppStrings.termsLabel)),
              ],
            );
          },
        ),
      ),
    );
  }
}
