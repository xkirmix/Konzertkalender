"""German date, time and count labels for the calendar image (independent of the system locale)."""

from __future__ import annotations

from datetime import date, datetime

WEEKDAY_NAMES = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
WEEKDAY_ABBREVIATIONS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")
MONTH_NAMES = (
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
)


class GermanCalendarLabels:
    @staticmethod
    def evening_heading(day: date) -> str:
        return f"{WEEKDAY_NAMES[day.weekday()]} {day.day}. {MONTH_NAMES[day.month - 1]}"

    @staticmethod
    def date_range(first: date, last: date) -> str:
        first_weekday = WEEKDAY_ABBREVIATIONS[first.weekday()]
        last_weekday = WEEKDAY_ABBREVIATIONS[last.weekday()]
        if first.month == last.month:
            return f"{first_weekday} {first.day}. – {last_weekday} {last.day}. {MONTH_NAMES[last.month - 1]} {last.year}"
        return (
            f"{first_weekday} {first.day}. {MONTH_NAMES[first.month - 1]} – "
            f"{last_weekday} {last.day}. {MONTH_NAMES[last.month - 1]} {last.year}"
        )

    @staticmethod
    def timestamp(moment: datetime) -> str:
        return f"{WEEKDAY_ABBREVIATIONS[moment.weekday()]} {moment:%d.%m.%Y, %H:%M}"

    @staticmethod
    def event_count(count: int) -> str:
        return "1 Event" if count == 1 else f"{count} Events"

    @staticmethod
    def hidden_events(count: int) -> str:
        return f"+ {count} weiteres Event" if count == 1 else f"+ {count} weitere Events"
