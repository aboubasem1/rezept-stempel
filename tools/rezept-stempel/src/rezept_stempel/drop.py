"""Pfade aus Drag-and-Drop, Verknüpfungen und Startargumenten."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def split_drop_payload(data: str) -> list[str]:
    """Zerlegt TkDnD-/Explorer-Payloads (`{C:\\Pfad mit Leerzeichen.pdf} ...`)."""
    items: list[str] = []
    buf: list[str] = []
    depth = 0
    i = 0
    while i < len(data):
        ch = data[i]
        if ch == "{" and depth == 0:
            depth = 1
        elif ch == "{" and depth > 0:
            depth += 1
            buf.append(ch)
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0:
                items.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
        elif ch in " \t\r\n" and depth == 0:
            if buf:
                items.append("".join(buf))
                buf = []
        elif ch == "\\" and depth == 0 and i + 1 < len(data) and data[i + 1] == " ":
            buf.append(" ")
            i += 1
        else:
            buf.append(ch)
        i += 1
    if buf:
        items.append("".join(buf))
    return [item for item in items if item]


def token_to_path(token: str) -> Path:
    raw = token.strip().strip('"').strip("'")
    if raw.lower().startswith("file:"):
        parsed = urlparse(raw)
        path = unquote(parsed.path)
        if parsed.netloc and parsed.netloc not in {"", "localhost"}:
            path = f"//{parsed.netloc}{path}"
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        raw = path
    if "\\" in raw:
        raw = raw.replace("\\", "/")
    return Path(raw)


def dropped_paths(data: object) -> list[Path]:
    if data is None:
        return []
    if isinstance(data, (list, tuple)):
        tokens: list[str] = []
        for item in data:
            if isinstance(item, bytes):
                tokens.append(item.decode(sys.getfilesystemencoding(), errors="replace"))
            else:
                tokens.extend(split_drop_payload(str(item)))
        return [token_to_path(token) for token in tokens]
    if isinstance(data, bytes):
        data = data.decode(sys.getfilesystemencoding(), errors="replace")
    return [token_to_path(token) for token in split_drop_payload(str(data))]


def collect_pdfs(paths: list[Path]) -> list[Path]:
    """Nur PDFs. Ordner: eine Ebene `*.pdf`, keine Rekursion."""
    found: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        candidates: list[Path]
        if path.is_dir():
            candidates = sorted(path.glob("*.pdf"))
        elif path.suffix.lower() == ".pdf":
            candidates = [path]
        else:
            continue
        for candidate in candidates:
            key = candidate.resolve() if candidate.exists() else candidate
            if key in seen:
                continue
            seen.add(key)
            found.append(candidate)
    return found
