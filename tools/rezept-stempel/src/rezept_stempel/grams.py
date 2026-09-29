"""Menge (x)g: 5 bis 100 in 5er-Schritten."""

from __future__ import annotations

MIN_GRAMS = 5
MAX_GRAMS = 100
STEP_GRAMS = 5
DEFAULT_GRAMS = 25


def clamp_grams(value: int) -> int:
    snapped = int(round(value / STEP_GRAMS) * STEP_GRAMS)
    return max(MIN_GRAMS, min(MAX_GRAMS, snapped))


def step_grams(current: int, direction: int) -> int:
    """direction > 0 erhöht, direction < 0 verringert, 0 lässt den Wert."""
    if direction == 0:
        return clamp_grams(current)
    step = STEP_GRAMS if direction > 0 else -STEP_GRAMS
    return clamp_grams(clamp_grams(current) + step)
