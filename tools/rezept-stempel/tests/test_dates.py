from datetime import datetime
from zoneinfo import ZoneInfo

from rezept_stempel.dates import BERLIN, filename_timestamp, overlay_date_text
from rezept_stempel.stamp import stamp_text


def test_overlay_date_is_berlin_dd_mm_yyyy() -> None:
    when = datetime(2026, 9, 29, 23, 30, tzinfo=ZoneInfo("UTC"))
    assert overlay_date_text(when) == "30.09.2026"


def test_filename_timestamp_is_berlin_compact() -> None:
    when = datetime(2026, 9, 29, 7, 5, tzinfo=BERLIN)
    assert filename_timestamp(when) == "2026-09-29_0705"


def test_stamp_text_format() -> None:
    when = datetime(2026, 3, 1, 12, 0, tzinfo=BERLIN)
    assert stamp_text(25, when) == "- 25g 01.03.2026"
