from rezept_stempel.layout import (
    DEFAULT_STAMP_X,
    DEFAULT_STAMP_Y,
    RX_ROW_TOPS,
    STAMP_FONTSIZE,
    click_to_baseline,
    default_stamp_point,
    overlay_rect,
    snap_rx_baseline,
    stamp_width,
)
from rezept_stempel.stamp import stamp_text


def test_default_stamp_sits_on_first_rx_row() -> None:
    x, y = default_stamp_point()
    assert x == DEFAULT_STAMP_X
    assert y == DEFAULT_STAMP_Y
    assert RX_ROW_TOPS[0] < y < RX_ROW_TOPS[0] + 20


def test_click_in_first_row_snaps_to_baseline() -> None:
    _x, y = click_to_baseline(200, 265)
    assert y == DEFAULT_STAMP_Y


def test_click_far_from_rows_keeps_position() -> None:
    assert snap_rx_baseline(500.0) == 500.0


def test_stamp_box_is_wider_than_text() -> None:
    text = stamp_text(25)
    width = stamp_width(text)
    assert width > 70
    box = overlay_rect(198, 252, text)
    assert box.width > width
    assert box.height > STAMP_FONTSIZE
