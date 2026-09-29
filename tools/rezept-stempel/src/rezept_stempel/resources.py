"""Laufzeitpfade: Quellbaum oder PyInstaller-Bundle."""

from __future__ import annotations

import sys
from pathlib import Path


def runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def sample_pdf_path() -> Path:
    return runtime_root() / "samples" / "TEST-REZEPT-0001.pdf"
