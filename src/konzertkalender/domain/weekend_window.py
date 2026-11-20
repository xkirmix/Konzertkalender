"""The Thursday-to-Saturday evening window that one calendar edition covers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from konzertkalender.domain.event import Event

THURSDAY_OFFSET = 3
SATURDAY_OFFSET = 5
SUNDAY_WEEKDAY = 6


@dataclass(frozen=True)
class WeekendWindow:
    """Evenings from `first_evening` (Thursday) to `last_evening` (Saturday), both inclusive.

    An event belongs to an evening if it starts at or after `evening_start_hour` that day, or
    after midnight but before `night_end_hour` (then it counts for the previous evening).
    """

    first_evening: date
    last_evening: date
    evening_start_hour: int = 17
    night_end_hour: int = 5

    @classmethod
    def for_reference_date(
        cls, reference: date, evening_start_hour: int = 17, night_end_hour: int = 5
    ) -> "WeekendWindow":
        """Monday to Saturday map to that week's Thursday-Saturday; Sunday maps to the next week."""
        monday = reference - timedelta(days=reference.weekday())
        if reference.weekday() == SUNDAY_WEEKDAY:
            monday += timedelta(days=7)
        return cls(
            first_evening=monday + timedelta(days=THURSDAY_OFFSET),
            last_evening=monday + timedelta(days=SATURDAY_OFFSET),
            evening_start_hour=evening_start_hour,
            night_end_hour=night_end_hour,
        )

    @property
    def evenings(self) -> list[date]:
        day_count = (self.last_evening - self.first_evening).days + 1
        return [self.first_evening + timedelta(days=offset) for offset in range(day_count)]

    def evening_of(self, moment: datetime) -> date | None:
        """The evening a start time belongs to, or None if it is outside the window."""
        if moment.hour >= self.evening_start_hour:
            evening = moment.date()
        elif moment.hour < self.night_end_hour:
            evening = moment.date() - timedelta(days=1)
        else:
            return None
        return evening if self.first_evening <= evening <= self.last_evening else None

    def covers_day(self, day: date) -> bool:
        """True if events on this calendar day can belong to the window (incl. Saturday night)."""
        return self.first_evening <= day <= self.last_evening + timedelta(days=1)

    def contains(self, event: Event) -> bool:
        return self.evening_of(event.starts_at) is not None
