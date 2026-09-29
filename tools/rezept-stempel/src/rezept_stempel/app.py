"""Deutschsprachige Desktop-Oberfläche zum Stempeln von Rezept-PDFs."""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pymupdf

from rezept_stempel.dates import now_berlin
from rezept_stempel.grams import DEFAULT_GRAMS, MAX_GRAMS, MIN_GRAMS, STEP_GRAMS, step_grams
from rezept_stempel.layout import (
    STAMP_COLOR,
    canvas_font_size,
    click_to_baseline,
    default_stamp_point,
)
from rezept_stempel.sample_pdf import default_sample_path
from rezept_stempel.stamp import Overlay, apply_overlays, stamp_text

PAPER = "#f6f2ea"
INK = "#1c1c1c"
MUTED = "#5a5a5a"
ACCENT = "#1e4d7b"


class RezeptStempelApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Rezept-Stempel")
        self.minsize(820, 640)
        self.configure(bg=PAPER)

        self.source_path: Path | None = None
        self.doc: pymupdf.Document | None = None
        self.page_index = 0
        self.zoom = 1.5
        self.grams = DEFAULT_GRAMS
        self.overlays: list[Overlay] = []
        self._page_image: tk.PhotoImage | None = None
        self._ghost: tuple[float, float] | None = None

        self._build_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_status("Keine Datei geöffnet. Wählen Sie ein Rezept-PDF über „PDF öffnen“.")

    def _build_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Toolbar.TFrame", background=PAPER)
        style.configure("TLabel", background=PAPER, foreground=INK)
        style.configure("Hint.TLabel", background=PAPER, foreground=MUTED, font=("TkDefaultFont", 9))
        style.configure("Stamp.TLabel", background=PAPER, foreground=ACCENT, font=("TkDefaultFont", 12, "bold"))
        style.configure("Status.TLabel", background="#e7e2d8", foreground=INK, padding=6)
        style.configure("Accent.TButton", font=("TkDefaultFont", 10, "bold"))

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, style="Toolbar.TFrame", padding=(12, 10, 12, 6))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="PDF öffnen", command=self.open_pdf, style="Accent.TButton").pack(side="left")
        ttk.Button(toolbar, text="Beispiel öffnen", command=self.open_sample).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Speichern", command=self.save_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Erste Rp-Zeile", command=self.place_default).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Letzten Stempel entfernen", command=self.undo_last).pack(side="left", padx=(8, 0))

        self.page_label = ttk.Label(toolbar, text="Seite —")
        self.page_label.pack(side="right")
        ttk.Button(toolbar, text="→", width=3, command=self.next_page).pack(side="right", padx=(4, 8))
        ttk.Button(toolbar, text="←", width=3, command=self.prev_page).pack(side="right")

        meta = ttk.Frame(self, style="Toolbar.TFrame", padding=(12, 0, 12, 8))
        meta.pack(fill="x")
        self.stamp_label = ttk.Label(meta, style="Stamp.TLabel")
        self.stamp_label.pack(anchor="w")
        ttk.Label(
            meta,
            style="Hint.TLabel",
            text=(
                f"Klick setzt den Stempel (auf Rp-Zeilen einrastend). "
                f"Mausrad: Menge {MIN_GRAMS}–{MAX_GRAMS} g in {STEP_GRAMS}er-Schritten. "
                "„Erste Rp-Zeile“ setzt die Standardposition. Speichern schreibt neben das Original."
            ),
        ).pack(anchor="w", pady=(4, 0))
        self._refresh_stamp_label()

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.canvas = tk.Canvas(body, background="#d8d3c8", highlightthickness=0, cursor="crosshair")
        vbar = ttk.Scrollbar(body, orient="vertical", command=self.canvas.yview)
        hbar = ttk.Scrollbar(body, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        self.empty_hint = self.canvas.create_text(
            400,
            280,
            text="Rezept-PDF öffnen, um den Stempel zu setzen.",
            fill=MUTED,
            font=("TkDefaultFont", 13),
        )

        self.status = ttk.Label(self, style="Status.TLabel", anchor="w")
        self.status.pack(fill="x")

        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.bind("<Control-o>", lambda _e: self.open_pdf())
        self.bind("<Control-s>", lambda _e: self.save_pdf())
        self.bind("<Control-z>", lambda _e: self.undo_last())
        self.bind("<Return>", lambda _e: self.place_default())
        self.bind("<Prior>", lambda _e: self.prev_page())
        self.bind("<Next>", lambda _e: self.next_page())
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>", lambda _e: self._nudge_grams(1))
        self.bind_all("<Button-5>", lambda _e: self._nudge_grams(-1))

    def _refresh_stamp_label(self) -> None:
        self.stamp_label.configure(text=f"Stempel:  {stamp_text(self.grams)}")

    def _set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def _nudge_grams(self, direction: int) -> str:
        self.grams = step_grams(self.grams, direction)
        if self.overlays:
            last = self.overlays[-1]
            last.grams = self.grams
            last.when = now_berlin()
        self._refresh_stamp_label()
        self._redraw_overlays()
        return "break"

    def _on_mousewheel(self, event: tk.Event) -> str:
        direction = 1 if getattr(event, "delta", 0) > 0 else -1
        return self._nudge_grams(direction)

    def open_pdf(self) -> None:
        chosen = filedialog.askopenfilename(
            title="Rezept-PDF öffnen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
        )
        if chosen:
            self._load_path(Path(chosen))

    def open_sample(self) -> None:
        sample = default_sample_path()
        if not sample.is_file():
            messagebox.showerror(
                "Beispiel fehlt",
                f"Die Musterdatei wurde nicht gefunden:\n{sample}",
            )
            return
        self._load_path(sample)

    def _load_path(self, path: Path) -> None:
        try:
            doc = pymupdf.open(path)
        except Exception as exc:  # noqa: BLE001 — Dateifehler an die Oberfläche
            messagebox.showerror("PDF konnte nicht geöffnet werden", str(exc))
            return
        if doc.is_encrypted:
            doc.close()
            messagebox.showerror("Geschützte Datei", "Passwortgeschützte PDFs werden nicht unterstützt.")
            return
        self._close_doc()
        self.doc = doc
        self.source_path = path
        self.page_index = 0
        self.overlays = []
        self._ghost = None
        self._render_page()
        self._set_status(
            f"Geöffnet: {path}  —  Klick oder „Erste Rp-Zeile“ setzt den Stempel, Speichern schreibt daneben."
        )

    def _close_doc(self) -> None:
        if self.doc is not None:
            self.doc.close()
            self.doc = None

    def _on_close(self) -> None:
        self._close_doc()
        self.destroy()

    def prev_page(self) -> None:
        if self.doc is None or self.page_index <= 0:
            return
        self.page_index -= 1
        self._render_page()

    def next_page(self) -> None:
        if self.doc is None or self.page_index >= self.doc.page_count - 1:
            return
        self.page_index += 1
        self._render_page()

    def _render_page(self) -> None:
        self.canvas.delete("all")
        self.empty_hint = None
        if self.doc is None:
            return
        page = self.doc[self.page_index]
        pix = page.get_pixmap(matrix=pymupdf.Matrix(self.zoom, self.zoom), alpha=False)
        self._page_image = tk.PhotoImage(data=pix.tobytes("ppm"))
        self.canvas.create_image(0, 0, anchor="nw", image=self._page_image, tags=("page",))
        self.canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
        self.page_label.configure(text=f"Seite {self.page_index + 1} / {self.doc.page_count}")
        self._redraw_overlays()

    def _canvas_point(self, event: tk.Event) -> tuple[float, float]:
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _pdf_point(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        return canvas_x / self.zoom, canvas_y / self.zoom

    def _on_click(self, event: tk.Event) -> None:
        if self.doc is None:
            self.open_pdf()
            return
        cx, cy = self._canvas_point(event)
        pdf_x, pdf_y = self._pdf_point(cx, cy)
        x, y = click_to_baseline(pdf_x, pdf_y)
        self.overlays.append(
            Overlay(
                page_index=self.page_index,
                x=x,
                y=y,
                grams=self.grams,
                when=now_berlin(),
            )
        )
        self._redraw_overlays()
        self._set_status(
            f"Stempel gesetzt: {stamp_text(self.grams)}  —  Mausrad ändert die Menge, Speichern schreibt die Datei."
        )

    def _on_motion(self, event: tk.Event) -> None:
        if self.doc is None:
            return
        self._ghost = self._canvas_point(event)
        self._redraw_overlays()

    def _on_leave(self, _event: tk.Event) -> None:
        self._ghost = None
        self._redraw_overlays()

    def _hex_stamp_color(self) -> str:
        r, g, b = STAMP_COLOR
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def _draw_stamp_visual(self, overlay: Overlay, fill: str) -> None:
        z = self.zoom
        rect = overlay.rect()
        self.canvas.create_rectangle(
            rect.x0 * z,
            rect.y0 * z,
            rect.x1 * z,
            rect.y1 * z,
            fill="white",
            outline="",
            tags=("stamp",),
        )
        self.canvas.create_text(
            overlay.x * z,
            overlay.y * z,
            text=overlay.text(),
            fill=fill,
            font=("Helvetica", canvas_font_size(z), "bold"),
            anchor="sw",
            tags=("stamp",),
        )

    def _redraw_overlays(self) -> None:
        self.canvas.delete("stamp")
        if self.doc is None:
            return
        ink = self._hex_stamp_color()
        for overlay in self.overlays:
            if overlay.page_index != self.page_index:
                continue
            self._draw_stamp_visual(overlay, ink)
        if self._ghost is not None:
            gx, gy = self._ghost
            pdf_x, pdf_y = self._pdf_point(gx, gy)
            x, y = click_to_baseline(pdf_x, pdf_y)
            ghost = Overlay(
                page_index=self.page_index,
                x=x,
                y=y,
                grams=self.grams,
                when=now_berlin(),
            )
            self._draw_stamp_visual(ghost, "#6b7280")
        elif not any(item.page_index == self.page_index for item in self.overlays):
            x, y = default_stamp_point()
            hint = Overlay(
                page_index=self.page_index,
                x=x,
                y=y,
                grams=self.grams,
                when=now_berlin(),
            )
            self._draw_stamp_visual(hint, "#9aa3af")

    def place_default(self) -> None:
        if self.doc is None:
            self.open_pdf()
            return
        x, y = default_stamp_point()
        overlay = Overlay(
            page_index=self.page_index,
            x=x,
            y=y,
            grams=self.grams,
            when=now_berlin(),
        )
        if self.overlays and self.overlays[-1].page_index == self.page_index:
            self.overlays[-1] = overlay
        else:
            self.overlays.append(overlay)
        self._redraw_overlays()
        self._set_status(
            f"Stempel auf der ersten Rp-Zeile: {overlay.text()}  —  Klick verschiebt nicht, setzt zusätzlich."
        )

    def undo_last(self) -> None:
        if not self.overlays:
            self._set_status("Kein Stempel zum Entfernen.")
            return
        removed = self.overlays.pop()
        self._redraw_overlays()
        self._set_status(f"Stempel entfernt: {removed.text()}")

    def save_pdf(self) -> None:
        if self.source_path is None or self.doc is None:
            messagebox.showinfo("Keine Datei", "Bitte zuerst ein Rezept-PDF öffnen.")
            return
        if not self.overlays:
            messagebox.showinfo("Kein Stempel", "Setzen Sie zuerst mit einem Klick mindestens einen Stempel.")
            return
        try:
            dest = apply_overlays(self.source_path, self.overlays)
        except Exception as exc:  # noqa: BLE001 — Speicherfehler an die Oberfläche
            messagebox.showerror("Speichern fehlgeschlagen", str(exc))
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self._set_status(f"Gespeichert neben dem Original: {dest}")
        messagebox.showinfo("Gespeichert", f"Die gestempelte Datei liegt im selben Ordner:\n{dest}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rezept-PDFs lokal stempeln und neben der Quelle speichern.")
    parser.add_argument("--open", type=Path, help="PDF beim Start öffnen")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    app = RezeptStempelApp()
    if args.open is not None:
        app._load_path(Path(args.open))
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
