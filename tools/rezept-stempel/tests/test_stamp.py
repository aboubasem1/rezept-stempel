from datetime import datetime
from pathlib import Path

from rezept_stempel.dates import BERLIN
from rezept_stempel.sample_pdf import write_sample_pdf
from rezept_stempel.stamp import Overlay, apply_overlays, extract_text, stamp_text


def test_save_writes_next_to_original_and_keeps_source(tmp_path: Path) -> None:
    source = write_sample_pdf(tmp_path / "TEST-REZEPT-0001.pdf")
    original = source.read_bytes()
    when = datetime(2026, 9, 29, 11, 58, tzinfo=BERLIN)
    overlay = Overlay(page_index=0, x=80, y=420, grams=25, when=when)
    dest = apply_overlays(source, [overlay])

    assert dest.parent == source.parent
    assert dest.name.startswith("TEST-REZEPT-0001_")
    assert dest.suffix == ".pdf"
    assert dest.is_file()
    assert source.read_bytes() == original
    stamped = extract_text(dest)
    assert stamp_text(25, when) in stamped
    assert "TEST-REZEPT-0001" in stamped
    assert original != dest.read_bytes()


def test_refuses_to_overwrite_source(tmp_path: Path) -> None:
    source = write_sample_pdf(tmp_path / "TEST-REZEPT-0001.pdf")
    overlay = Overlay(page_index=0, x=80, y=420, grams=10)
    try:
        apply_overlays(source, [overlay], dest=source)
    except ValueError as exc:
        assert "überschrieben" in str(exc)
    else:
        raise AssertionError("Quelle darf nicht überschrieben werden")
