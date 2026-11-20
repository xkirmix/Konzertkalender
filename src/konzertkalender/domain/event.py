"""Core event model shared by all venue sources, the selection and the rendering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventKind(Enum):
    """What kind of evening an event is; used for filtering and shown as a label."""

    CONCERT = "konzert"
    PARTY = "party"
    OTHER = "andere"

    @property
    def label(self) -> str:
        return _KIND_LABELS[self]

    @classmethod
    def from_config_value(cls, value: str) -> "EventKind":
        """Maps a config value like "konzert" to its kind; raises ValueError for unknown values."""
        return cls(value.strip().lower())


_KIND_LABELS = {EventKind.CONCERT: "Konzert", EventKind.PARTY: "Party", EventKind.OTHER: "Event"}


@dataclass(frozen=True)
class Event:
    """A single event at a venue. `starts_at` is timezone-aware local time (Europe/Zurich)."""

    venue: str
    title: str
    starts_at: datetime
    kind: EventKind
    genres: tuple[str, ...] = ()
    url: str | None = None
    has_start_time: bool = True
    is_cancelled: bool = False
    club: str = ""  # the club whose program listed it, e.g. "PROGR" for "PROGR Turnhalle"
