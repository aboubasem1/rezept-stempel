from pathlib import Path

import pymupdf

from rezept_stempel.layout import DEFAULT_STAMP_Y, PAGE_HEIGHT, PAGE_WIDTH, RX_ROW_TOPS
from rezept_stempel.sample_pdf import SAMPLE_ID, write_sample_pdf
from rezept_stempel.stamp import extract_text

FORBIDDEN = (
    "Müller",
    "Schmidt",
    "Mustermann",
    "Max ",
    "Cannaleo Patient",
)


def test_sample_uses_only_test_identifiers(tmp_path: Path) -> None:
    path = write_sample_pdf(tmp_path / f"{SAMPLE_ID}.pdf")
    text = extract_text(path)
    assert SAMPLE_ID in text
    assert "TEST-PATIENT-0001" in text
    assert "TEST-PREPARAT" in text
    assert "TEST-EXTRAKT" in text
    assert "TEST-ARZT-0001" in text
    assert "Rp." in text
    for token in FORBIDDEN:
        assert token not in text


def test_sample_page_matches_kassenrezept_geometry(tmp_path: Path) -> None:
    path = write_sample_pdf(tmp_path / f"{SAMPLE_ID}.pdf")

    doc = pymupdf.open(path)
    try:
        page = doc[0]
        assert abs(page.rect.width - PAGE_WIDTH) < 0.1
        assert abs(page.rect.height - PAGE_HEIGHT) < 0.1
        words = page.get_text("words")
        preparat = [w for w in words if "TEST-PREPARAT" in w[4]]
        assert preparat
        _x0, y0, _x1, y1, *_rest = preparat[0]
        assert RX_ROW_TOPS[0] - 2 <= y0 <= DEFAULT_STAMP_Y
        assert y1 <= RX_ROW_TOPS[0] + 24
    finally:
        doc.close()
