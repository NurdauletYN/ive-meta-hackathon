"""Deterministic design-direction checks: WCAG AA + hue/typography diversity."""

from __future__ import annotations

import colorsys

from preflight.checks import contrast_ratio

from pilot.schemas import Direction


def hex_hue(value: str) -> float:
    raw = value.lstrip("#")
    r = int(raw[0:2], 16) / 255.0
    g = int(raw[2:4], 16) / 255.0
    b = int(raw[4:6], 16) / 255.0
    h, _s, _v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360.0


def hue_delta(a: float, b: float) -> float:
    delta = abs(a - b) % 360.0
    return min(delta, 360.0 - delta)


def contrast_errors(direction: Direction) -> list[str]:
    errors: list[str] = []
    for pair in direction.tokens.contrast_pairs:
        ratio = contrast_ratio(pair.foreground, pair.background)
        if ratio < 4.5:
            errors.append(
                f"{direction.name} pair {pair.name}: contrast {ratio:.2f} < 4.5 "
                f"({pair.foreground} on {pair.background})"
            )
    return errors


def diversity_errors(directions: list[Direction]) -> list[str]:
    errors: list[str] = []
    hues = [hex_hue(d.tokens.colors.primary) for d in directions]
    for i in range(len(hues)):
        for j in range(i + 1, len(hues)):
            delta = hue_delta(hues[i], hues[j])
            if delta < 40:
                errors.append(
                    f"primary hue {directions[i].name} vs {directions[j].name}: "
                    f"{delta:.1f} deg < 40"
                )
    radii = {round(d.tokens.corner_radius, 2) for d in directions}
    types = {d.tokens.typography for d in directions}
    if len(radii) < 2 and len(types) < 2:
        errors.append("need at least two distinct corner_radius or typography values across directions")
    return errors
