"""Erzeugt eine Muster-Rezept-PDF nur mit TEST-Kennungen."""

from __future__ import annotations

from pathlib import Path

import pymupdf

SAMPLE_ID = "TEST-REZEPT-0001"
SAMPLE_FILENAME = f"{SAMPLE_ID}.pdf"

# Nur synthetische Kennungen — keine realen Patientendaten.
SAMPLE_LINES = (
    "KASSENREZEPT  ·  Testdaten",
    SAMPLE_ID,
    "",
    "Dieses Dokument enthält ausschließlich TEST-Kennungen.",
    "Kein reales Rezept, kein realer Patient, keine echte Verordnung.",
    "",
    "Krankenkasse          TEST-KASSE-0001",
    "Versicherten-Nr.      TEST-VNR-0001",
    "Status                Test",
    "",
    "Name                  TEST-PATIENT-0001",
    "Anschrift             TEST-STRASSE 1, 00000 TEST-ORT",
    "Geburtsdatum          01.01.1990 (Testdatum)",
    "",
    "Rp",
    "",
    "  1.  TEST-PREPARAT 10 mg",
    "  2.  TEST-CANNABIS-EXTRAKT 25 mg/ml",
    "",
    "Platz für Apothekenvermerk (Menge / Datum) unterhalb der Positionen.",
    "",
    "Arzt                  TEST-ARZT-0001",
    "Betriebsstätten-Nr.   TEST-BSNR-0001",
    "LANR                  TEST-LANR-0001",
    "Ausstellungsdatum     01.01.2026 (Testdatum)",
)


def default_sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "samples" / SAMPLE_FILENAME


def write_sample_pdf(dest: Path | None = None) -> Path:
    dest = Path(dest) if dest is not None else default_sample_path()
    dest.parent.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open()
    try:
        page = doc.new_page(width=595, height=842)
        margin = 48
        page.draw_rect(pymupdf.Rect(margin, margin, 595 - margin, 842 - margin), color=(0.08, 0.16, 0.38), width=1.2)
        page.draw_rect(pymupdf.Rect(margin + 8, margin + 8, 595 - margin - 8, 842 - margin - 8), color=(0.08, 0.16, 0.38), width=0.4)

        y = margin + 36
        page.insert_text((margin + 24, y), SAMPLE_LINES[0], fontsize=11, fontname="hebo", color=(0.08, 0.16, 0.38))
        y += 22
        page.insert_text((margin + 24, y), SAMPLE_LINES[1], fontsize=16, fontname="hebo", color=(0.08, 0.16, 0.38))
        y += 18
        page.draw_line(pymupdf.Point(margin + 24, y), pymupdf.Point(595 - margin - 24, y), color=(0.08, 0.16, 0.38), width=0.6)
        y += 28

        for line in SAMPLE_LINES[2:]:
            if line == "Rp":
                page.insert_text((margin + 24, y), line, fontsize=18, fontname="hebo", color=(0.08, 0.16, 0.38))
                y += 26
                continue
            page.insert_text((margin + 24, y), line, fontsize=11, fontname="helv", color=(0.12, 0.12, 0.14))
            y += 16

        page.insert_text(
            (margin + 24, 842 - margin - 20),
            "TEST-APOTHEKE Musterstadt  ·  TEST-IK-0001",
            fontsize=9,
            fontname="helv",
            color=(0.25, 0.25, 0.28),
        )
        doc.save(dest, deflate=True)
    finally:
        doc.close()
    return dest


def main() -> int:
    path = write_sample_pdf()
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
