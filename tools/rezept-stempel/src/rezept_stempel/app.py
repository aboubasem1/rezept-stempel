"""Deutschsprachige Desktop-Oberfläche zum Stempeln von Rezept-PDFs."""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pymupdf

from rezept_stempel.dates import now_berlin
from rezept_stempel.dnd import enable_file_drop
from rezept_stempel.drop import collect_pdfs
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
DROP_HINT = "PDFs hierher ziehen — oder über „PDF öffnen“ wählen."


@dataclass
class DocumentSession:
    path: Path
    overlays: list[Overlay] = field(default_factory=list)
    page_index: int = 0


class RezeptStempelApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Rezept-Stempel")
        self.minsize(960, 640)
        self.configure(bg=PAPER)

        self.sessions: dict[Path, DocumentSession] = {}
        self._order: list[Path] = []
        self.source_path: Path | None = None
        self.doc: pymupdf.Document | None = None
        self.page_index = 0
        self.zoom = 1.5
        self.grams = DEFAULT_GRAMS
        self.overlays: list[Overlay] = []
        self._page_image: tk.PhotoImage | None = None
        self._ghost: tuple[float, float] | None = None
        self._syncing_list = False

        self._build_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_status("Bereit. PDFs auf das Fenster ziehen oder über „PDF öffnen“ wählen.")
        self.after_idle(self._install_drop)

    def _install_drop(self) -> None:
        kind = enable_file_drop(self, self.open_paths)
        if kind == "tkdnd":
            enable_file_drop(self.canvas, self.open_paths)
            enable_file_drop(self.file_list, self.open_paths)
        if kind == "none" and self.source_path is None:
            self._set_status(
                "PDFs auf die Desktop-Verknüpfung ziehen oder „PDF öffnen“. "
                "Drop ins Fenster: Windows-Build (build.ps1) oder pip install -e \".[desktop]\"."
            )

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
        style.configure("Sidebar.TFrame", background=PAPER)

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
                "PDFs per Drag & Drop öffnen. Klick setzt den Stempel (Rp-Zeilen rasten ein). "
                f"Mausrad: {MIN_GRAMS}–{MAX_GRAMS} g in {STEP_GRAMS}er-Schritten. "
                "Speichern schreibt neben das Original, ohne es zu überschreiben."
            ),
        ).pack(anchor="w", pady=(4, 0))
        self._refresh_stamp_label()

        mid = ttk.Frame(self)
        mid.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        mid.columnconfigure(1, weight=1)
        mid.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(mid, style="Sidebar.TFrame", padding=(0, 0, 10, 0))
        sidebar.grid(row=0, column=0, sticky="nsw")
        ttk.Label(sidebar, text="Offene Dateien").pack(anchor="w")
        ttk.Label(sidebar, style="Hint.TLabel", text="Mehrere PDFs ablegen möglich").pack(anchor="w", pady=(0, 4))
        self.file_list = tk.Listbox(
            sidebar,
            width=28,
            height=24,
            activestyle="dotbox",
            selectmode="browse",
            background="#fffdf8",
            highlightthickness=1,
            highlightbackground="#cfc8bb",
        )
        self.file_list.pack(fill="y", expand=True)
        self.file_list.bind("<<ListboxSelect>>", self._on_list_select)
        ttk.Button(sidebar, text="Aktuelle schließen", command=self.close_current).pack(anchor="w", pady=(6, 0))

        body = ttk.Frame(mid)
        body.grid(row=0, column=1, sticky="nsew")
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
            420,
            280,
            text=DROP_HINT,
            fill=MUTED,
            font=("TkDefaultFont", 13),
            width=520,
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
        chosen = filedialog.askopenfilenames(
            title="Rezept-PDFs öffnen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")],
        )
        if chosen:
            self.open_paths([Path(item) for item in chosen])

    def open_sample(self) -> None:
        sample = default_sample_path()
        if not sample.is_file():
            messagebox.showerror(
                "Beispiel fehlt",
                f"Die Musterdatei wurde nicht gefunden:\n{sample}",
            )
            return
        self.open_paths([sample])

    def open_paths(self, paths: list[Path]) -> None:
        pdfs = collect_pdfs(list(paths))
        if not pdfs:
            messagebox.showinfo("Keine PDF", "Bitte eine oder mehrere PDF-Dateien ablegen (oder einen Ordner mit PDFs).")
            return
        errors: list[str] = []
        first: Path | None = None
        for path in pdfs:
            try:
                key = self._add_pdf(path)
            except Exception as exc:  # noqa: BLE001 — Dateifehler an die Oberfläche
                errors.append(f"{path.name}: {exc}")
                continue
            if first is None:
                first = key
        if first is not None:
            self._show(first)
        self._refresh_file_list()
        if errors:
            messagebox.showerror("Einige Dateien konnten nicht geöffnet werden", "\n".join(errors[:8]))

    def _add_pdf(self, path: Path) -> Path:
        path = path.expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Datei nicht gefunden: {path}")
        key = path.resolve()
        if key.suffix.lower() != ".pdf":
            raise ValueError("Nur PDF-Dateien.")
        if key in self.sessions:
            return key
        doc = pymupdf.open(key)
        try:
            if doc.is_encrypted:
                raise ValueError("Passwortgeschützte PDFs werden nicht unterstützt.")
        finally:
            doc.close()
        self.sessions[key] = DocumentSession(path=key)
        self._order.append(key)
        return key

    def _stash(self) -> None:
        if self.source_path is None:
            return
        key = self.source_path.resolve()
        session = self.sessions.get(key)
        if session is None:
            return
        session.overlays = list(self.overlays)
        session.page_index = self.page_index

    def _show(self, key: Path) -> None:
        self._stash()
        session = self.sessions[key]
        self._close_doc()
        self.doc = pymupdf.open(session.path)
        self.source_path = session.path
        self.overlays = list(session.overlays)
        self.page_index = session.page_index
        self._ghost = None
        self._render_page()
        self._set_status(
            f"Geöffnet: {session.path}  —  Stempel setzen, Speichern schreibt daneben."
        )

    def _refresh_file_list(self) -> None:
        self._syncing_list = True
        self.file_list.delete(0, "end")
        current = self.source_path.resolve() if self.source_path is not None else None
        select = 0
        for index, key in enumerate(self._order):
            self.file_list.insert("end", key.name)
            if key == current:
                select = index
        if self._order:
            self.file_list.selection_set(select)
            self.file_list.see(select)
        self._syncing_list = False

    def _on_list_select(self, _event: tk.Event) -> None:
        if self._syncing_list:
            return
        selection = self.file_list.curselection()
        if not selection:
            return
        key = self._order[int(selection[0])]
        if self.source_path is None or key != self.source_path.resolve():
            self._show(key)
            self._refresh_file_list()

    def close_current(self) -> None:
        if self.source_path is None:
            return
        key = self.source_path.resolve()
        self._close_doc()
        self.source_path = None
        self.overlays = []
        self.page_index = 0
        self.sessions.pop(key, None)
        if key in self._order:
            self._order.remove(key)
        if self._order:
            self._show(self._order[0])
        else:
            self.canvas.delete("all")
            self.empty_hint = self.canvas.create_text(
                420, 280, text=DROP_HINT, fill=MUTED, font=("TkDefaultFont", 13), width=520
            )
            self.page_label.configure(text="Seite —")
            self._set_status("Keine Datei geöffnet. PDFs hierher ziehen.")
        self._refresh_file_list()

    def _load_path(self, path: Path) -> None:
        """Kompatibilität für Tests und --open."""
        self.open_paths([path])

    def _close_doc(self) -> None:
        if self.doc is not None:
            doc = self.doc
            self.doc = None
            doc.close()

    def _on_close(self) -> None:
        self._stash()
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
        self._set_status(f"Stempel auf der ersten Rp-Zeile: {overlay.text()}")

    def undo_last(self) -> None:
        if not self.overlays:
            self._set_status("Kein Stempel zum Entfernen.")
            return
        removed = self.overlays.pop()
        self._redraw_overlays()
        self._set_status(f"Stempel entfernt: {removed.text()}")

    def save_pdf(self) -> None:
        if self.source_path is None or self.doc is None:
            messagebox.showinfo("Keine Datei", "Bitte zuerst ein Rezept-PDF öffnen oder hierher ziehen.")
            return
        if not self.overlays:
            messagebox.showinfo("Kein Stempel", "Setzen Sie zuerst mit einem Klick mindestens einen Stempel.")
            return
        self._stash()
        try:
            dest = apply_overlays(self.source_path, self.overlays)
        except Exception as exc:  # noqa: BLE001 — Speicherfehler an die Oberfläche
            messagebox.showerror("Speichern fehlgeschlagen", str(exc))
            self._set_status(f"Speichern fehlgeschlagen: {exc}")
            return
        self._set_status(f"Gespeichert neben dem Original: {dest}")
        messagebox.showinfo("Gespeichert", f"Die gestempelte Datei liegt im selben Ordner:\n{dest}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rezept-PDFs lokal stempeln und neben der Quelle speichern."
    )
    parser.add_argument("--open", type=Path, action="append", default=[], help="PDF beim Start öffnen")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="PDF-Dateien (auch per Drag & Drop auf die EXE/Verknüpfung)",
    )
    return parser.parse_args(argv)


def startup_paths(args: argparse.Namespace) -> list[Path]:
    return list(args.open) + list(args.files)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    app = RezeptStempelApp()
    paths = startup_paths(args)
    if paths:
        app.open_paths(paths)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
