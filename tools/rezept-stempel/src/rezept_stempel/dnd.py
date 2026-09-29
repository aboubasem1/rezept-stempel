"""Dateidrop auf das Fenster (TkDnD, Windows WM_DROPFILES)."""

from __future__ import annotations

import sys
import tkinter as tk
from collections.abc import Callable
from pathlib import Path

from rezept_stempel.drop import collect_pdfs, dropped_paths

DropCallback = Callable[[list[Path]], None]


def enable_file_drop(widget: tk.Misc, on_pdfs: DropCallback) -> str:
    """Installiert einen Drop-Empfänger. Rückgabe: 'tkdnd' | 'win32' | 'none'."""
    if _enable_tkdnd(widget, on_pdfs):
        return "tkdnd"
    if sys.platform == "win32" and _enable_win32_drop(widget, on_pdfs):
        return "win32"
    return "none"


def _deliver(on_pdfs: DropCallback, data: object) -> None:
    pdfs = collect_pdfs(dropped_paths(data))
    on_pdfs(pdfs)


def _enable_tkdnd(widget: tk.Misc, on_pdfs: DropCallback) -> bool:
    try:
        from tkinterdnd2 import DND_FILES
        from tkinterdnd2.TkinterDnD import _require
    except Exception:
        return False
    try:
        _require(widget)
        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", lambda event: _deliver(on_pdfs, event.data))
        return True
    except Exception:
        return False


def _enable_win32_drop(widget: tk.Misc, on_pdfs: DropCallback) -> bool:
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return False

    wm_dropfiles = 0x0233
    gwlp_wndproc = -4
    lresult = ctypes.c_ssize_t
    wndproc_t = ctypes.WINFUNCTYPE(
        lresult, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    shell32 = ctypes.WinDLL("shell32", use_last_error=True)
    user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongPtrW.restype = ctypes.c_void_p
    user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    user32.SetWindowLongPtrW.restype = ctypes.c_void_p
    user32.CallWindowProcW.argtypes = [
        ctypes.c_void_p,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    user32.CallWindowProcW.restype = lresult
    shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
    shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
    shell32.DragQueryFileW.restype = wintypes.UINT
    shell32.DragFinish.argtypes = [wintypes.HANDLE]

    hwnd = int(widget.winfo_id())
    if hwnd == 0:
        return False
    shell32.DragAcceptFiles(hwnd, True)
    old_proc = user32.GetWindowLongPtrW(hwnd, gwlp_wndproc)
    if not old_proc:
        return False

    def _handle(hwnd_: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == wm_dropfiles:
            count = int(shell32.DragQueryFileW(wparam, 0xFFFFFFFF, None, 0))
            tokens: list[str] = []
            buf = ctypes.create_unicode_buffer(1024)
            for index in range(count):
                length = shell32.DragQueryFileW(wparam, index, buf, 1024)
                if length:
                    tokens.append(buf.value)
            shell32.DragFinish(wparam)
            widget.after(0, lambda captured=list(tokens): _deliver(on_pdfs, captured))
            return 0
        return int(user32.CallWindowProcW(old_proc, hwnd_, msg, wparam, lparam))

    wrapped = wndproc_t(_handle)
    widget._rezept_stempel_wndproc = wrapped  # noqa: SLF001 — muss vor GC geschützt werden
    user32.SetWindowLongPtrW(hwnd, gwlp_wndproc, ctypes.cast(wrapped, ctypes.c_void_p).value)
    return True
