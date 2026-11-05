import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';

import '../kit/kit.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _Slide {
  const _Slide(this.title, this.body);

  final String title;
  final String body;
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  late final Future<Map<String, String>> _slots = _loadSlots();
  int _page = 0;

  Future<Map<String, String>> _loadSlots() async {
    final raw = await rootBundle.loadString(
      'assets/onboarding/onboarding.json',
    );
    final json = jsonDecode(raw) as Map<String, dynamic>;
    final slots = json['slots'] as Map<String, dynamic>;
    return slots.map((key, value) => MapEntry(key, value as String));
  }

  List<_Slide> _slides(Map<String, String> slots) {
    final out = <_Slide>[
      _Slide(slots['hero_title'] ?? '', slots['hero_body'] ?? ''),
    ];
    for (final prefix in const ['slide2', 'slide3']) {
      final title = slots['${prefix}_title'];
      if (title != null && title.isNotEmpty) {
        out.add(_Slide(title, slots['${prefix}_body'] ?? ''));
      }
    }
    return out;
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: scheme.surface,
      body: FutureBuilder<Map<String, String>>(
        future: _slots,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final slots = snapshot.data!;
          final slides = _slides(slots);
          final hint = slots['hero_hint'] ?? slots['hero_title'] ?? '';
          final start = KitPhoto.names.indexOf(
            KitPhoto.resolve(
              title: hint,
            ).split('/').last.replaceAll('.jpg', ''),
          );
          final last = _page == slides.length - 1;
          return Stack(
            children: [
              Positioned.fill(
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        scheme.primary.withValues(alpha: 0.32),
                        scheme.surface,
                      ],
                      stops: const [0, 0.6],
                    ),
                  ),
                ),
              ),
              SafeArea(
                child: Column(
                  children: [
                    Align(
                      alignment: Alignment.centerRight,
                      child: Padding(
                        padding: EdgeInsets.only(
                          right: tokens.spacing.sm,
                          top: tokens.spacing.xs,
                        ),
                        child: TextButton(
                          onPressed: () => context.go('/signup'),
                          child: Text(
                            'Skip',
                            style: TextStyle(
                              color: scheme.onSurface.withValues(alpha: 0.6),
                            ),
                          ),
                        ),
                      ),
                    ),
                    Expanded(
                      child: PageView.builder(
                        controller: _controller,
                        itemCount: slides.length,
                        onPageChanged: (value) => setState(() => _page = value),
                        itemBuilder: (context, index) => _SlidePage(
                          slide: slides[index],
                          photos: [
                            KitPhoto.path(
                              KitPhoto.names[(math.max(start, 0) + index * 5) %
                                  KitPhoto.names.length],
                            ),
                            KitPhoto.path(
                              KitPhoto.names[(math.max(start, 0) +
                                      index * 5 +
                                      7) %
                                  KitPhoto.names.length],
                            ),
                            KitPhoto.path(
                              KitPhoto.names[(math.max(start, 0) +
                                      index * 5 +
                                      13) %
                                  KitPhoto.names.length],
                            ),
                          ],
                        ),
                      ),
                    ),
                    Padding(
                      padding: EdgeInsets.fromLTRB(
                        tokens.spacing.lg,
                        0,
                        tokens.spacing.lg,
                        tokens.spacing.lg,
                      ),
                      child: Column(
                        children: [
                          if (slides.length > 1)
                            Padding(
                              padding: EdgeInsets.only(
                                bottom: tokens.spacing.md,
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  for (var i = 0; i < slides.length; i++)
                                    AnimatedContainer(
                                      duration: const Duration(
                                        milliseconds: 240,
                                      ),
                                      curve: Curves.easeOutCubic,
                                      margin: const EdgeInsets.symmetric(
                                        horizontal: 3,
                                      ),
                                      width: i == _page ? 26 : 8,
                                      height: 8,
                                      decoration: BoxDecoration(
                                        color: i == _page
                                            ? scheme.primary
                                            : scheme.onSurface.withValues(
                                                alpha: 0.18,
                                              ),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                          PrimaryButton(
                            label: last ? 'Continue' : 'Next',
                            onPressed: () {
                              if (last) {
                                context.go('/signup');
                              } else {
                                _controller.nextPage(
                                  duration: const Duration(milliseconds: 320),
                                  curve: Curves.easeOutCubic,
                                );
                              }
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _SlidePage extends StatelessWidget {
  const _SlidePage({required this.slide, required this.photos});

  final _Slide slide;
  final List<String> photos;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: tokens.spacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Reveal(
              child: Center(
                child: AspectRatio(
                  aspectRatio: 1,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      _Tilted(
                        angle: -0.12,
                        dx: -0.32,
                        dy: 0.06,
                        photo: photos[1],
                        scale: 0.58,
                      ),
                      _Tilted(
                        angle: 0.11,
                        dx: 0.32,
                        dy: -0.04,
                        photo: photos[2],
                        scale: 0.58,
                      ),
                      _Tilted(
                        angle: 0.0,
                        dx: 0,
                        dy: 0,
                        photo: photos[0],
                        scale: 0.7,
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
          SizedBox(height: tokens.spacing.lg),
          Reveal(
            index: 1,
            child: Text(
              slide.title,
              style: TextStyle(
                fontSize: tokens.typeScale.display * 1.3,
                fontWeight: FontWeight.w700,
                height: 1.05,
                letterSpacing: -1.1,
                color: scheme.onSurface,
              ),
            ),
          ),
          SizedBox(height: tokens.spacing.sm),
          Reveal(
            index: 2,
            child: Text(
              slide.body,
              style: TextStyle(
                fontSize: tokens.typeScale.body,
                height: 1.4,
                color: scheme.onSurface.withValues(alpha: 0.66),
              ),
            ),
          ),
          SizedBox(height: tokens.spacing.lg),
        ],
      ),
    );
  }
}

class _Tilted extends StatelessWidget {
  const _Tilted({
    required this.angle,
    required this.dx,
    required this.dy,
    required this.photo,
    required this.scale,
  });

  final double angle;
  final double dx;
  final double dy;
  final String photo;
  final double scale;

  @override
  Widget build(BuildContext context) {
    final tokens = KitTokens.of(context);
    return LayoutBuilder(
      builder: (context, box) {
        final side = math.min(box.maxWidth, box.maxHeight) * scale;
        return Transform.translate(
          offset: Offset(dx * box.maxWidth * 0.5, dy * box.maxHeight * 0.5),
          child: Transform.rotate(
            angle: angle,
            child: Container(
              width: side,
              height: side,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(tokens.radii.lg + 6),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.28),
                    blurRadius: 30,
                    offset: const Offset(0, 16),
                  ),
                ],
              ),
              child: KitPhotoTile(title: photo, photo: photo, size: null),
            ),
          ),
        );
      },
    );
  }
}
