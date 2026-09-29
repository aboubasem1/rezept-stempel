"""Ausgabe neben der Quelldatei — kein Browser-Download."""

from __future__ import annotations

from pathlib import Path

from rezept_stempel.dates import filename_timestamp, now_berlin


def stamped_output_path(source: Path, when=None) -> Path:
    """Zielpfad im selben Ordner: stamm_YYYY-MM-DD_HHMM.pdf."""
    source = Path(source)
    if source.suffix.lower() != ".pdf":
        raise ValueError("Quelle muss eine PDF-Datei sein.")
    stamp = filename_timestamp(now_berlin(when))
    candidate = source.with_name(f"{source.stem}_{stamp}.pdf")
    if candidate.resolve() == source.resolve():
        raise ValueError("Zieldatei darf die Quelle nicht überschreiben.")
    return _unique_beside(source, candidate)


def _unique_beside(source: Path, candidate: Path) -> Path:
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    parent = candidate.parent
    index = 2
    while True:
        nxt = parent / f"{stem}-{index}{suffix}"
        if nxt.resolve() == source.resolve():
            index += 1
            continue
        if not nxt.exists():
            return nxt
        index += 1
        if index > 999:
            raise OSError("Kein freier Dateiname neben der Quelle.")
