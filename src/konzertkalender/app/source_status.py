"""How each venue source fared during an update (shown in the footer and in kalender.json)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceStatus:
    venue_name: str
    event_count: int = 0
    error: str | None = None

    @property
    def is_healthy(self) -> bool:
        """A source that throws or suddenly finds nothing at all most likely needs a parser fix."""
        return self.error is None and self.event_count > 0
