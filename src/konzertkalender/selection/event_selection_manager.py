"""Filters, de-duplicates, sorts and groups events into the weekend program.

Within an evening the events are ordered by club (in the configured order of the clubs), then by
start time.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner


class EventSelectionManager:
    """Keeps evening events of the configured kinds inside the window, one entry per event."""

    def __init__(self, included_kinds: Iterable[EventKind], club_order: Sequence[str] = ()) -> None:
        self._included_kinds = frozenset(included_kinds)
        self._club_rank = {club: rank for rank, club in enumerate(club_order)}

    def select(self, events: Iterable[Event], window: WeekendWindow) -> WeekendProgram:
        relevant = [event for event in events if self._is_relevant(event, window)]
        grouped: dict[date, list[Event]] = {evening: [] for evening in window.evenings}
        for event in sorted(self._deduplicate(relevant), key=self._sort_key):
            grouped[window.evening_of(event.starts_at)].append(event)
        return WeekendProgram(window=window, events_by_evening={day: tuple(found) for day, found in grouped.items()})

    def _is_relevant(self, event: Event, window: WeekendWindow) -> bool:
        return event.kind in self._included_kinds and not event.is_cancelled and window.contains(event)

    @staticmethod
    def _deduplicate(events: list[Event]) -> list[Event]:
        """Same venue, same start and same title (ignoring case/accents) counts as one event."""
        unique: dict[tuple[str, object, str], Event] = {}
        for event in events:
            key = (event.venue, event.starts_at, TextCleaner.fold(event.title))
            unique.setdefault(key, event)
        return list(unique.values())

    def _sort_key(self, event: Event) -> tuple[object, ...]:
        club = event.club or event.venue
        return (self._club_rank.get(club, len(self._club_rank)), club, event.starts_at, event.title)
