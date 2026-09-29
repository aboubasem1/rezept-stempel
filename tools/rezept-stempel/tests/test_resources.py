from rezept_stempel.resources import runtime_root, sample_pdf_path


def test_sample_path_is_test_only() -> None:
    path = sample_pdf_path()
    assert path.name == "TEST-REZEPT-0001.pdf"
    assert "TEST-" in path.name
    root = runtime_root()
    assert path == root / "samples" / "TEST-REZEPT-0001.pdf"
