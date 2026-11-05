import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../app/strings.dart';
import '../billing/billing_service.dart';
import '../billing/offering_product.dart';
import '../kit/kit.dart';
import 'subscription_disclosure.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key, required this.billing});

  final BillingService billing;

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> {
  late final Future<List<OfferingProduct>> _offerings = widget.billing
      .offerings();

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
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return RocketScaffold(
      showBottomNav: false,
      body: FutureBuilder<List<OfferingProduct>>(
        future: _offerings,
        builder: (context, snapshot) {
          final items = snapshot.data ?? const <OfferingProduct>[];
          return SingleChildScrollView(
            padding: EdgeInsets.fromLTRB(
              tokens.spacing.md,
              0,
              tokens.spacing.md,
              tokens.spacing.xl,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Reveal(
                  child: HeroHeader(
                    title: AppStrings.paywallTitle,
                    subtitle:
                        'Unlock the full app. Cancel any time in your App Store settings.',
                    photo: KitPhoto.path('watch'),
                    actionLabel: 'Plus',
                  ),
                ),
                SizedBox(height: tokens.spacing.md),
                Reveal(
                  index: 1,
                  child: ListSection(
                    children: const [
                      ListRow(title: 'Everything unlocked', emoji: '🔓'),
                      ListRow(title: 'Restore on any device', emoji: '📲'),
                      ListRow(title: 'Cancel in two taps', emoji: '🛑'),
                    ],
                  ),
                ),
                SizedBox(height: tokens.spacing.md),
                for (final product in items)
                  Padding(
                    padding: EdgeInsets.only(bottom: tokens.spacing.sm),
                    child: Reveal(
                      index: 2,
                      child: Material(
                        color: scheme.surfaceContainerHighest,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(tokens.radii.lg),
                          side: BorderSide(color: scheme.primary, width: 1.5),
                        ),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(tokens.radii.lg),
                          onTap: () => _subscribe(product.id),
                          child: Padding(
                            padding: EdgeInsets.all(tokens.spacing.md),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    product.title,
                                    style: TextStyle(
                                      fontSize: tokens.typeScale.body,
                                      fontWeight: FontWeight.w700,
                                      color: scheme.onSurface,
                                    ),
                                  ),
                                ),
                                PriceTag(text: product.priceLabel),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                SizedBox(height: tokens.spacing.sm),
                const SubscriptionDisclosure(),
                SizedBox(height: tokens.spacing.md),
                PrimaryButton(
                  label: AppStrings.subscribeLabel,
                  onPressed: () =>
                      _subscribe(items.isNotEmpty ? items.first.id : null),
                ),
                SizedBox(height: tokens.spacing.sm),
                Wrap(
                  alignment: WrapAlignment.center,
                  children: [
                    TextButton(
                      onPressed: () => widget.billing.restorePurchases(),
                      child: const Text(AppStrings.restoreLabel),
                    ),
                    TextButton(
                      onPressed: () => context.push('/privacy'),
                      child: const Text(AppStrings.privacyLabel),
                    ),
                    TextButton(
                      onPressed: () => context.push('/terms'),
                      child: const Text(AppStrings.termsLabel),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
