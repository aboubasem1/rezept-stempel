from pathlib import Path

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
    assert "TEST-ARZT-0001" in text
    for token in FORBIDDEN:
        assert token not in text
