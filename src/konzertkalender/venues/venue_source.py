"""The contract every venue source fulfils."""

from __future__ import annotations

from typing import Protocol

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow


class VenueSource(Protocol):
    """Reads a venue's published program.

    Sources may return events outside the window (the selection filters them); the window is
    passed so sources can limit expensive detail-page requests to the relevant days.
    """

    venue_name: str

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        ...
