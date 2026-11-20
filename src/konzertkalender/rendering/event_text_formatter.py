"""The text pieces shown for one event: start time, club, title and the room/kind/genre line."""

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
        """The exact venue, e.g. "PROGR Turnhalle"."""
        return event.venue

    @staticmethod
    def club_label(event: Event) -> str:
        """The club whose program lists the event, e.g. "PROGR" (the venue if no club is known)."""
        return event.club or event.venue

    @classmethod
    def room_label(cls, event: Event) -> str:
        """The room inside the club, if the venue names one: "PROGR Turnhalle" -> "Turnhalle",
        "bee-flat (PROGR)" -> "bee-flat"; empty when the venue is the club itself."""
        club, venue = cls.club_label(event), event.venue
        if venue == club:
            return ""
        if venue.startswith(club):
            return venue[len(club):].strip(" -–·")
        if venue.endswith(f"({club})"):
            return venue[: -len(club) - 2].strip()
        return venue

    @classmethod
    def details_label(cls, event: Event) -> str:
        """ "Turnhalle · Party · House": the line under the title."""
        parts = (cls.room_label(event), event.kind.label, ", ".join(event.genres))
        return META_SEPARATOR.join(part for part in parts if part)

    @classmethod
    def compact_details_label(cls, event: Event) -> str:
        """ "Turnhalle · House" for one-line rows: the genres say enough, so the kind only appears
        when there are no genres ("Party")."""
        parts = (cls.room_label(event), ", ".join(event.genres) or event.kind.label)
        return META_SEPARATOR.join(part for part in parts if part)
