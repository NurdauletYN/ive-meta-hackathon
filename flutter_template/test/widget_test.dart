import 'package:flutter_test/flutter_test.dart';
import 'package:rocket_capsule/app/strings.dart';

void main() {
  test('app name is set', () {
    expect(AppStrings.appName, isNotEmpty);
  });
}
