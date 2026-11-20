"""The selected events of one weekend, grouped by evening, ready to be rendered."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow


@dataclass(frozen=True)
class WeekendProgram:
    window: WeekendWindow
    events_by_evening: dict[date, tuple[Event, ...]]

    def events_on(self, evening: date) -> tuple[Event, ...]:
        return self.events_by_evening.get(evening, ())

    @property
    def event_count(self) -> int:
        return sum(len(events) for events in self.events_by_evening.values())
