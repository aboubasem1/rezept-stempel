from datetime import datetime
from pathlib import Path

from rezept_stempel.dates import BERLIN
from rezept_stempel.paths import stamped_output_path


def test_output_sits_beside_source(tmp_path: Path) -> None:
    source = tmp_path / "TEST-REZEPT-0001.pdf"
    source.write_bytes(b"%PDF-1.4")
    when = datetime(2026, 9, 29, 14, 7, tzinfo=BERLIN)
    dest = stamped_output_path(source, when)
    assert dest.parent == source.parent
    assert dest.name == "TEST-REZEPT-0001_2026-09-29_1407.pdf"
    assert dest != source


def test_collision_gets_suffix_not_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "blatt.pdf"
    source.write_bytes(b"%PDF-1.4")
    when = datetime(2026, 9, 29, 14, 7, tzinfo=BERLIN)
    taken = tmp_path / "blatt_2026-09-29_1407.pdf"
    taken.write_bytes(b"taken")
    dest = stamped_output_path(source, when)
    assert dest == tmp_path / "blatt_2026-09-29_1407-2.pdf"
    assert not dest.exists()
    assert taken.read_bytes() == b"taken"
    assert source.read_bytes() == b"%PDF-1.4"
