"""Machine-readable form of an edition (kalender.json) for checking and later reuse."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.footer_info import FooterInfo


class ProgramSerializer:
    def to_dict(self, program: WeekendProgram, footer: FooterInfo, statuses: Sequence[SourceStatus]) -> dict[str, Any]:
        return {
            "erstellt": footer.generated_at.isoformat(timespec="minutes"),
            "wochenende": {
                "von": program.window.first_evening.isoformat(),
                "bis": program.window.last_evening.isoformat(),
            },
            "abende": {
                evening.isoformat(): [self._event(event) for event in program.events_on(evening)]
                for evening in program.window.evenings
            },
            "quellen": [self._status(status) for status in statuses],
        }

    @staticmethod
    def _event(event: Event) -> dict[str, Any]:
        return {
            "club": event.venue,
            "titel": event.title,
            "beginn": event.starts_at.isoformat(timespec="minutes") if event.has_start_time else None,
            "datum": event.starts_at.date().isoformat(),
            "art": event.kind.value,
            "genres": list(event.genres),
            "link": event.url,
        }

    @staticmethod
    def _status(status: SourceStatus) -> dict[str, Any]:
        return {"club": status.venue_name, "events": status.event_count, "ok": status.is_healthy, "fehler": status.error}
