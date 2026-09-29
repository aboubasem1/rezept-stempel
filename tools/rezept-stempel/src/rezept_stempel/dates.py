"""Datums- und Zeitstempel in Europe/Berlin."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def now_berlin(when: datetime | None = None) -> datetime:
    if when is None:
        return datetime.now(BERLIN)
    if when.tzinfo is None:
        return when.replace(tzinfo=BERLIN)
    return when.astimezone(BERLIN)


def overlay_date_text(when: datetime | None = None) -> str:
    """Datum auf dem Stempel: DD.MM.YYYY."""
    return now_berlin(when).strftime("%d.%m.%Y")


def filename_timestamp(when: datetime | None = None) -> str:
    """Zeitstempel im Dateinamen: YYYY-MM-DD_HHMM."""
    return now_berlin(when).strftime("%Y-%m-%d_%H%M")
