import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../kit/kit.dart';
import 'auth_service.dart';

class SignUpScreen extends StatefulWidget {
  const SignUpScreen({super.key, required this.auth});

  final AuthService auth;

  @override
  State<SignUpScreen> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  String? _error;
  bool _busy = false;
  bool _signIn = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _error = null;
      _busy = true;
    });
    try {
      if (_signIn) {
        await widget.auth.signIn(email: _email.text.trim(), password: _password.text);
      } else {
        await widget.auth.signUp(email: _email.text.trim(), password: _password.text);
      }
      if (mounted) context.go('/home');
    } catch (err) {
      if (mounted) setState(() => _error = 'Could not continue. Check the email and password.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return RocketScaffold(
      title: _signIn ? 'Sign in' : 'Sign up',
      showBottomNav: false,
      body: ListView(
        padding: EdgeInsets.all(tokens.spacing.lg),
        children: [
          HeroHeader(
            title: _signIn ? 'Welcome back' : 'Create your account',
            subtitle: 'Email and password. You can delete the account later in Settings.',
            emoji: '🔑',
          ),
          SizedBox(height: tokens.spacing.lg),
          AppTextField(
            controller: _email,
            label: 'Email',
            hint: 'you@example.com',
            keyboardType: TextInputType.emailAddress,
          ),
          SizedBox(height: tokens.spacing.md),
          AppTextField(
            controller: _password,
            label: 'Password',
            obscureText: true,
          ),
          if (_error != null) ...[
            SizedBox(height: tokens.spacing.sm),
            Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
          ],
          SizedBox(height: tokens.spacing.lg),
          PrimaryButton(label: _busy ? 'Working…' : (_signIn ? 'Sign in' : 'Create account'), onPressed: _busy ? null : _submit),
          SizedBox(height: tokens.spacing.sm),
          SecondaryButton(
            label: _signIn ? 'Need an account? Sign up' : 'Already have an account? Sign in',
            onPressed: () => setState(() => _signIn = !_signIn),
          ),
        ],
      ),
    );
  }
}
