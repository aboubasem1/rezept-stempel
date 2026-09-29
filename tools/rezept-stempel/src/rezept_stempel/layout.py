"""Typische A4-Kassenrezept-Geometrie in PDF-Punkten.

Nur Layout — keine Patientendaten. Die Werte beschreiben ein gedrucktes
e-Rezept / Kassenrezept: Rp-Bereich ab y≈210, drei Verordnungszeilen
im Abstand von ~58 pt. Der Apothekenvermerk sitzt auf der Zeile, oft
mit weißem Untergrund über dem gedruckten Text.
"""

from __future__ import annotations

import pymupdf

PAGE_WIDTH = 595.28
PAGE_HEIGHT = 841.89

STAMP_FONTSIZE = 11
STAMP_FONT = "hebo"
STAMP_COLOR = (0.05, 0.14, 0.40)
STAMP_PAD_X = 2.4
STAMP_PAD_Y = 1.4
STAMP_ASCENT = STAMP_FONTSIZE * 0.80
STAMP_DESCENT = STAMP_FONTSIZE * 0.22

# Erste von drei Verordnungsblöcken (Oberkante) und Zeilenabstand.
RX_ROW_TOPS = (240.0, 298.2, 356.4)
RX_ROW_HEIGHT = 46.6
# Nach einem typischen Präparatenamen; Baseline der ersten Rp-Zeile.
DEFAULT_STAMP_X = 198.0
DEFAULT_STAMP_Y = RX_ROW_TOPS[0] + 12.0  # 252.0


def stamp_width(text: str) -> float:
    return pymupdf.get_text_length(text, fontname=STAMP_FONT, fontsize=STAMP_FONTSIZE)


def overlay_rect(x: float, y: float, text: str) -> pymupdf.Rect:
    """Weißes Untergrund-Rechteck um den Stempel (x/y = Text-Baseline links)."""
    return pymupdf.Rect(
        x - STAMP_PAD_X,
        y - STAMP_ASCENT - STAMP_PAD_Y,
        x + stamp_width(text) + STAMP_PAD_X,
        y + STAMP_DESCENT + STAMP_PAD_Y,
    )


def click_to_baseline(click_x: float, click_y: float) -> tuple[float, float]:
    """Klick in einer Rp-Zeile rastet auf deren Baseline; sonst Klick = Stempelmitte."""
    snapped = snap_click_to_rx_row(click_y)
    if snapped is not None:
        return click_x, snapped
    baseline = click_y + (STAMP_ASCENT - STAMP_DESCENT) / 2.0
    return click_x, baseline


def snap_click_to_rx_row(click_y: float) -> float | None:
    for top in RX_ROW_TOPS:
        if top - 4.0 <= click_y <= top + RX_ROW_HEIGHT + 4.0:
            return top + 12.0
    return None


def snap_rx_baseline(y: float) -> float:
    """Zieht eine Baseline in eine Rp-Zeile, falls sie in deren Band liegt."""
    snapped = snap_click_to_rx_row(y)
    return y if snapped is None else snapped


def default_stamp_point() -> tuple[float, float]:
    return DEFAULT_STAMP_X, DEFAULT_STAMP_Y


def canvas_font_size(zoom: float) -> int:
    return max(9, int(round(STAMP_FONTSIZE * zoom)))
