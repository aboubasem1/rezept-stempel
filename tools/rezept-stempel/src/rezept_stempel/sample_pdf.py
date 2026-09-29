"""Erzeugt eine Muster-Rezept-PDF nur mit TEST-Kennungen.

Das Layout folgt einem typischen A4-Kassenrezept (Rp-Bereich, drei
Verordnungszeilen), ohne Inhalte aus realen Rezepten zu übernehmen.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from rezept_stempel.layout import (
    DEFAULT_STAMP_X,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    RX_ROW_HEIGHT,
    RX_ROW_TOPS,
)

SAMPLE_ID = "TEST-REZEPT-0001"
SAMPLE_FILENAME = f"{SAMPLE_ID}.pdf"

NAVY = (0.08, 0.16, 0.38)
INK = (0.12, 0.12, 0.14)
RULE = (0.55, 0.58, 0.62)

RX_ITEMS = (
    ("1.", "TEST-PREPARAT 10 mg", "TEST-PZN-0001"),
    ("2.", "TEST-EXTRAKT 25 mg/ml", "TEST-PZN-0002"),
    ("3.", "TEST-HILFSMITTEL A", "TEST-PZN-0003"),
)


def default_sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "samples" / SAMPLE_FILENAME


def write_sample_pdf(dest: Path | None = None) -> Path:
    dest = Path(dest) if dest is not None else default_sample_path()
    dest.parent.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open()
    try:
        page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        _draw_form(page)
        doc.save(dest, deflate=True)
    finally:
        doc.close()
    return dest


def _draw_form(page: pymupdf.Page) -> None:
    page.draw_rect(pymupdf.Rect(18, 18, PAGE_WIDTH - 18, PAGE_HEIGHT - 18), color=NAVY, width=1.0)

    page.insert_text((30, 58), "Krankenkasse", fontsize=8, fontname="helv", color=INK)
    page.insert_text((30, 70), "TEST-KASSE-0001", fontsize=9, fontname="hebo", color=NAVY)
    page.insert_text((340, 58), "Bezugsdatum", fontsize=8, fontname="helv", color=INK)
    page.insert_text((340, 70), "01.01.2026", fontsize=9, fontname="helv", color=INK)
    page.insert_text((483, 58), "Apotheken-Nr.", fontsize=8, fontname="helv", color=INK)
    page.insert_text((483, 70), "TEST-IK-0001", fontsize=9, fontname="helv", color=INK)

    page.insert_text((30, 98), "Versicherte Person (Testdaten, kein realer Patient)", fontsize=8, fontname="helv", color=INK)
    page.insert_text((30, 111), "TEST-PATIENT-0001", fontsize=9, fontname="hebo", color=NAVY)
    page.insert_text((30, 124), "TEST-VNR-0001", fontsize=9, fontname="helv", color=INK)
    page.insert_text((30, 137), "TEST-STRASSE 1, 00000 TEST-ORT", fontsize=9, fontname="helv", color=INK)
    page.insert_text((270, 109), "geb. am", fontsize=8, fontname="helv", color=INK)
    page.insert_text((270, 122), "01.01.1990", fontsize=9, fontname="helv", color=INK)
    page.insert_text((340, 129), "Arzneimittel-Nr.", fontsize=8, fontname="helv", color=INK)
    page.insert_text((340, 142), "TEST-AMNR-0001", fontsize=9, fontname="helv", color=INK)

    page.draw_line(pymupdf.Point(30, 168), pymupdf.Point(PAGE_WIDTH - 30, 168), color=RULE, width=0.5)
    page.insert_text((30, 188), SAMPLE_ID, fontsize=11, fontname="hebo", color=NAVY)
    page.insert_text((30, 202), "Nur TEST-Kennungen. Kein reales Rezept.", fontsize=8, fontname="helv", color=INK)

    page.insert_text((30, 224), "Rp.", fontsize=12, fontname="hebo", color=NAVY)
    page.insert_text((270, 209), "Datum", fontsize=8, fontname="helv", color=INK)
    page.insert_text((270, 224), "01.01.2026", fontsize=12, fontname="helv", color=INK)

    for (marker, name, pzn), top in zip(RX_ITEMS, RX_ROW_TOPS, strict=True):
        band = pymupdf.Rect(28, top, PAGE_WIDTH - 160, top + RX_ROW_HEIGHT)
        page.draw_rect(band, color=RULE, width=0.35)
        page.insert_text((34, top + 14), f"{marker}  {name}", fontsize=10, fontname="helv", color=INK)
        page.insert_text((34, top + 28), pzn, fontsize=9, fontname="helv", color=INK)
        page.insert_text((34, top + 40), "gedruckte Menge", fontsize=8, fontname="helv", color=(0.45, 0.45, 0.48))

    # Markiert die Standardposition der ersten Zeile, ohne denselben Text zu stempeln.
    guide_x = DEFAULT_STAMP_X
    page.insert_text((guide_x, RX_ROW_TOPS[0] + 40), "Standardposition →", fontsize=7, fontname="helv", color=(0.55, 0.2, 0.2))

    page.insert_text((382, 436), "ausstellende Person", fontsize=8, fontname="helv", color=INK)
    page.insert_text((382, 450), "TEST-ARZT-0001", fontsize=9, fontname="hebo", color=NAVY)
    page.insert_text((382, 464), "TEST-BSNR-0001 · TEST-LANR-0001", fontsize=8, fontname="helv", color=INK)
    page.insert_text((220, 516), "TEST-APOTHEKE Musterstadt", fontsize=8, fontname="helv", color=INK)
    page.insert_text((390, 516), "Unterschrift des Arztes", fontsize=8, fontname="helv", color=INK)


def main() -> int:
    path = write_sample_pdf()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
