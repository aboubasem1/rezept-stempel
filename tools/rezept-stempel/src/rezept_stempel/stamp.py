"""Text-Overlay und Schreiben der gestempelten PDF."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pymupdf

from rezept_stempel.dates import overlay_date_text
from rezept_stempel.grams import clamp_grams
from rezept_stempel.paths import stamped_output_path

STAMP_FONTSIZE = 12
STAMP_COLOR = (0.08, 0.16, 0.38)
STAMP_FONT = "helv"


def stamp_text(grams: int, when: datetime | None = None) -> str:
    return f"- {clamp_grams(grams)}g {overlay_date_text(when)}"


@dataclass
class Overlay:
    page_index: int
    x: float
    y: float
    grams: int
    when: datetime | None = None

    def text(self) -> str:
        return stamp_text(self.grams, self.when)


def apply_overlays(source: Path, overlays: list[Overlay], dest: Path | None = None) -> Path:
    """Schreibt eine neue PDF neben der Quelle. Die Originaldatei bleibt unverändert."""
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(f"PDF nicht gefunden: {source}")
    if dest is None:
        dest = stamped_output_path(source)
    dest = Path(dest)
    if dest.resolve() == source.resolve():
        raise ValueError("Die Quelldatei darf nicht überschrieben werden.")
    dest.parent.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(source)
    try:
        if doc.is_encrypted:
            raise ValueError("Passwortgeschützte PDFs werden nicht unterstützt.")
        for overlay in overlays:
            if overlay.page_index < 0 or overlay.page_index >= doc.page_count:
                raise IndexError(f"Seite {overlay.page_index + 1} fehlt in der PDF.")
            page = doc[overlay.page_index]
            page.insert_text(
                (overlay.x, overlay.y),
                overlay.text(),
                fontsize=STAMP_FONTSIZE,
                fontname=STAMP_FONT,
                color=STAMP_COLOR,
            )
        doc.save(dest, deflate=True, garbage=3)
    finally:
        doc.close()
    return dest


def extract_text(path: Path) -> str:
    doc = pymupdf.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()
