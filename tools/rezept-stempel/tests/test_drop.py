from pathlib import Path

from rezept_stempel.app import parse_args, startup_paths
from rezept_stempel.drop import collect_pdfs, dropped_paths, split_drop_payload, token_to_path


def test_split_braced_windows_paths() -> None:
    payload = r"{C:\Rezepte\TEST-REZEPT-0001.pdf} {C:\Rezepte\zweite datei.pdf}"
    parts = split_drop_payload(payload)
    assert parts[0].endswith("TEST-REZEPT-0001.pdf")
    assert parts[1].endswith("zweite datei.pdf")


def test_file_uri_windows_drive() -> None:
    path = token_to_path("file:///C:/Temp/TEST-REZEPT-0001.pdf")
    assert str(path) == r"C:\Temp\TEST-REZEPT-0001.pdf" or str(path) == "C:/Temp/TEST-REZEPT-0001.pdf"


def test_dropped_paths_from_list() -> None:
    paths = dropped_paths([r"D:\a.pdf", b"D:\\b.pdf"])
    assert [p.name for p in paths] == ["a.pdf", "b.pdf"]


def test_collect_pdfs_filters_and_folder(tmp_path: Path) -> None:
    pdf = tmp_path / "TEST-REZEPT-0001.pdf"
    other = tmp_path / "notes.txt"
    pdf.write_bytes(b"%PDF-1.4")
    other.write_text("nope", encoding="utf-8")
    nested = tmp_path / "subdir"
    nested.mkdir()
    (nested / "skip.pdf").write_bytes(b"%PDF-1.4")
    found = collect_pdfs([tmp_path, other])
    assert found == [pdf]


def test_startup_paths_merge_open_and_positional() -> None:
    args = parse_args(["--open", "a.pdf", "b.pdf", "c.pdf"])
    paths = startup_paths(args)
    assert [p.name for p in paths] == ["a.pdf", "b.pdf", "c.pdf"]
