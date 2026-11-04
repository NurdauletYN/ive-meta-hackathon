# RevenueCat billing adapter (unverified)

`RevenueCatBillingService` implements the capsule `BillingService` (`purchase`, `restorePurchases`, `offerings`) using `purchases_flutter`. It is selected at startup **only** when a user-supplied **public** SDK key is present:

- `revenuecat_api_key.txt` at the Flutter project root (first non-comment line), or
- `lib/revenuecat_key.dart` defining `revenueCatPublicApiKey = '...'`, or
- `--dart-define=REVENUECAT_API_KEY=...` at build time

Those filenames are gitignored. Do not commit them. The harness never passes them to a Pilot.

If none of those are present, the app uses `MockBillingService` and Settings shows a **demo mode** label. The paywall still renders the mock offering list. That fallback is what `harness gate` exercises.

Restore purchases is wired on Settings and on the paywall. Both call `BillingService.restorePurchases()`.

## What you must set up (outside this repo)

These steps are yours. This repository does not call App Store Connect or RevenueCat.

1. **App Store Connect:** create the app record (the public API cannot create apps). Complete the Paid Applications agreement, banking, and tax. Create a subscription group and at least one auto-renewable subscription product. Note the product id.
2. **Sandbox tester:** create an Apple ID in Users and Access → Sandbox.
3. **RevenueCat:** create a project. Add an iOS app with this bundle id. Attach App Store Connect credentials in RevenueCat (that is done in their dashboard, not by this harness). Create an **offering** whose packages map to the App Store product ids.
4. **Public SDK key:** copy the **public** Apple API key (`appl_…`) from RevenueCat into `revenuecat_api_key.txt`. That key is designed for the client app. Still do not commit it.
5. Build and run on a **real device** or a StoreKit sandbox, signed into the sandbox tester. Complete a purchase and a restore.

## Unverified

This adapter is **unverified** until a sandbox purchase is completed on a real device. Offline tests inject a **fake** gateway and make **no live calls**. They do not prove StoreKit, App Store receipt validation, offering availability, or restore-purchases against Apple.
