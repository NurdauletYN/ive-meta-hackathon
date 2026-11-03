import 'package:flutter/material.dart';

/// Subscription disclosure required beside the purchase CTA (price, period, auto-renew, cancel).
class SubscriptionDisclosure extends StatelessWidget {
  const SubscriptionDisclosure({super.key});

  @override
  Widget build(BuildContext context) {
    return const Text(
      'Rocket Plus: \$4.99 per month, auto-renews until canceled. '
      'Cancel anytime in device subscription settings.',
      style: TextStyle(fontSize: 13),
    );
  }
}
