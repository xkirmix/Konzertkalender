"""Which events of an evening start a new club group (the program is already sorted by club).

Shared by the image layout and the list page, so both group the same way.
"""

from __future__ import annotations

from collections.abc import Sequence

from konzertkalender.domain.event import Event
from konzertkalender.rendering.event_text_formatter import EventTextFormatter


class ClubGrouping:
    def __init__(self, formatter: EventTextFormatter) -> None:
        self._formatter = formatter

    def group_starts(self, events: Sequence[Event]) -> tuple[bool, ...]:
        """True for every event whose club differs from the event before it."""
        starts, previous_club = [], None
        for event in events:
            club = self._formatter.club_label(event)
            starts.append(club != previous_club)
            previous_club = club
        return tuple(starts)
