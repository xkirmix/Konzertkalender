"""The text pieces shown for one event: start time, title and the venue/kind/genre line."""

from __future__ import annotations

from konzertkalender.domain.event import Event

META_SEPARATOR = " · "
UNKNOWN_TIME = "–"


class EventTextFormatter:
    @staticmethod
    def time_label(event: Event) -> str:
        return f"{event.starts_at:%H:%M}" if event.has_start_time else UNKNOWN_TIME

    @staticmethod
    def venue_label(event: Event) -> str:
        return event.venue

    @staticmethod
    def details_label(event: Event) -> str:
        """ " · Konzert · Garage Rock, Trash Punk" (follows the venue on the same line)."""
        parts = [event.kind.label]
        if event.genres:
            parts.append(", ".join(event.genres))
        return META_SEPARATOR + META_SEPARATOR.join(parts)
