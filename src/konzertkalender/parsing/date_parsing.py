"""Parsing German and French date/time snippets from venue websites, including year inference."""

from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta

MONTH_NUMBERS = {
    "jan": 1, "januar": 1, "janvier": 1, "january": 1,
    "feb": 2, "februar": 2, "fevrier": 2, "février": 2, "fev": 2, "fév": 2, "févr": 2, "february": 2,
    "mär": 3, "mar": 3, "märz": 3, "maerz": 3, "mars": 3, "march": 3,
    "apr": 4, "april": 4, "avril": 4, "avr": 4,
    "mai": 5, "may": 5,
    "jun": 6, "juni": 6, "juin": 6, "june": 6,
    "jul": 7, "juli": 7, "juillet": 7, "juil": 7, "july": 7,
    "aug": 8, "august": 8, "août": 8, "aout": 8,
    "sep": 9, "sept": 9, "september": 9, "septembre": 9,
    "okt": 10, "oct": 10, "oktober": 10, "octobre": 10, "october": 10,
    "nov": 11, "november": 11, "novembre": 11,
    "dez": 12, "dec": 12, "déc": 12, "dezember": 12, "décembre": 12, "decembre": 12, "december": 12,
}

NUMERIC_DATE = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4}|\d{2})?(?!\d)")
NAMED_MONTH_DATE = re.compile(r"(?<!\d)(\d{1,2})\.?\s+([^\W\d_]+)\.?(?:\s+(\d{4}))?")
TIME_OF_DAY = re.compile(
    r"(?<![\d.])([01]?\d|2[0-3])"
    r"(?:\s*[:h]\s*([0-5]\d)(?!\d)"  # 20:00, 20h30
    r"|\.([0-5]\d)\s*Uhr"  # 20.00 Uhr
    r"|\s*(?:Uhr|h)(?![^\W\d_]|\d)"  # 22 Uhr, 21h
    r"|(?=\s*[–-]\s*\d{1,2}(?::\d{2})?\s*Uhr))"  # 16–19 Uhr (start of a range)
)
ISO_DATE_TIME = re.compile(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?")
RELATIVE_DAY_OFFSETS = {"heute": 0, "aujourd'hui": 0, "today": 0, "morgen": 1, "demain": 1, "tomorrow": 1}


class YearResolver:
    """Infers the year of a day and month without a year.

    Takes the earliest occurrence that is not more than `max_days_in_past` before the
    reference date (listings often still show events of the last weeks).
    """

    def __init__(self, reference: date, max_days_in_past: int = 60) -> None:
        self._reference = reference
        self._earliest_allowed = reference - timedelta(days=max_days_in_past)

    def resolve(self, month: int, day: int) -> date | None:
        for year in (self._reference.year - 1, self._reference.year, self._reference.year + 1):
            try:
                candidate = date(year, month, day)
            except ValueError:
                continue
            if candidate >= self._earliest_allowed:
                return candidate
        return None


class VenueDateParser:
    """Turns the date and time formats used by the venues into `date` and `time` objects."""

    def __init__(self, reference: date) -> None:
        self._reference = reference
        self._years = YearResolver(reference)

    def numeric_date(self, text: str) -> date | None:
        """ "Fr. 20.11.2026", "20.11.26" or "27.11." (year inferred)."""
        match = NUMERIC_DATE.search(text or "")
        if not match:
            return None
        day, month, year_text = int(match.group(1)), int(match.group(2)), match.group(3)
        return self._build_date(day, month, year_text)

    def named_month_date(self, text: str) -> date | None:
        """ "So., 22. Nov. 2026", "Freitag 20 November 2026", "samedi 21 novembre"."""
        for match in NAMED_MONTH_DATE.finditer(text or ""):
            month = self.month_number(match.group(2))
            if month is not None:
                return self._build_date(int(match.group(1)), month, match.group(3))
        return None

    def relative_day(self, text: str) -> date | None:
        """ "Heute" / "Morgen" (and French/English equivalents) relative to the reference date."""
        offset = RELATIVE_DAY_OFFSETS.get((text or "").strip().lower())
        return self._reference + timedelta(days=offset) if offset is not None else None

    def time_of_day(self, text: str) -> time | None:
        """First time in the text: "20:00", "20h30", "20.00 Uhr", "22 Uhr"."""
        match = TIME_OF_DAY.search(text or "")
        if not match:
            return None
        minute_text = match.group(2) or match.group(3) or "0"
        return time(int(match.group(1)), int(minute_text))

    def labeled_time(self, text: str, labels: tuple[str, ...]) -> time | None:
        """Time that follows one of the labels, e.g. "Start 20:00" in "Tür 19:30, Start 20:00"."""
        for label in labels:
            position = (text or "").lower().find(label.lower())
            if position >= 0:
                found = self.time_of_day(text[position + len(label):])
                if found is not None:
                    return found
        return None

    def iso_date_and_time(self, text: str) -> tuple[date, time | None] | None:
        """Date and wall-clock time from "2026-11-27 20:00:00" or "2026-11-20T20:00:00-08:00".

        Any UTC offset is ignored on purpose: several venues publish local times with wrong offsets.
        """
        match = ISO_DATE_TIME.search(text or "")
        if not match:
            return None
        day = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        clock = time(int(match.group(4)), int(match.group(5))) if match.group(4) else None
        return day, clock

    @staticmethod
    def aware_datetime(text: str | None) -> datetime | None:
        """Timezone-aware datetime from a correct ISO 8601 string (e.g. schema.org startDate)."""
        try:
            parsed = datetime.fromisoformat((text or "").strip())
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else None

    def _build_date(self, day: int, month: int, year_text: str | None) -> date | None:
        if not year_text:
            return self._years.resolve(month, day)
        year = int(year_text) + (2000 if len(year_text) == 2 else 0)
        try:
            return date(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def month_number(word: str) -> int | None:
        """Month number for German, French or English names and abbreviations ("Nov", "déc.")."""
        lowered = (word or "").strip().lower().rstrip(".")
        return MONTH_NUMBERS.get(lowered) or MONTH_NUMBERS.get(lowered[:4]) or MONTH_NUMBERS.get(lowered[:3])
