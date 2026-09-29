# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für die Windows-EXE (ohne Konsole). Auf Windows bauen."""

from __future__ import annotations

import os

from PyInstaller.utils.hooks import collect_all

SPECDIR = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.abspath(os.path.join(SPECDIR, "..", ".."))
SRC = os.path.join(ROOT, "src")
ENTRY = os.path.join(SRC, "rezept_stempel", "__main__.py")
SAMPLE = os.path.join(ROOT, "samples", "TEST-REZEPT-0001.pdf")

pymupdf_datas, pymupdf_binaries, pymupdf_hidden = collect_all("pymupdf")

try:
    tkdnd_datas, tkdnd_binaries, tkdnd_hidden = collect_all("tkinterdnd2")
except Exception:
    tkdnd_datas, tkdnd_binaries, tkdnd_hidden = [], [], []

a = Analysis(
    [ENTRY],
    pathex=[SRC],
    binaries=pymupdf_binaries + tkdnd_binaries,
    datas=pymupdf_datas
    + tkdnd_datas
    + ([(SAMPLE, "samples")] if os.path.isfile(SAMPLE) else []),
    hiddenimports=["pymupdf", "tkinter", "tkinter.filedialog", "tkinter.messagebox", "tkinter.ttk"]
    + pymupdf_hidden
    + tkdnd_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Rezept-Stempel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
