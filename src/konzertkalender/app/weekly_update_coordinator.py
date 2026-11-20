"""The weekly update flow: read all venues, select the weekend, render and publish."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.rendered_calendar import RenderedCalendar
from konzertkalender.selection.event_selection_manager import EventSelectionManager
from konzertkalender.venues.venue_source import VenueSource

LOGGER = logging.getLogger(__name__)


class CalendarRenderer(Protocol):
    def render(self, program: WeekendProgram, footer: FooterInfo) -> RenderedCalendar: ...


class EditionPublisher(Protocol):
    def publish(
        self, calendar: RenderedCalendar, program: WeekendProgram, footer: FooterInfo, statuses: Sequence[SourceStatus]
    ) -> list[Path]: ...


@dataclass(frozen=True)
class UpdateReport:
    program: WeekendProgram
    statuses: tuple[SourceStatus, ...]
    written_files: tuple[Path, ...]

    @property
    def all_sources_failed(self) -> bool:
        return not any(status.is_healthy for status in self.statuses)


class WeeklyUpdateCoordinator:
    def __init__(
        self,
        sources: Sequence[VenueSource],
        selection: EventSelectionManager,
        renderer: CalendarRenderer,
        publisher: EditionPublisher,
        clock: Callable[[], datetime],
        window_for_date: Callable[[date], WeekendWindow],
    ) -> None:
        self._sources = sources
        self._selection = selection
        self._renderer = renderer
        self._publisher = publisher
        self._clock = clock
        self._window_for_date = window_for_date

    def run(self, reference_date: date | None = None) -> UpdateReport:
        """Builds the edition for the weekend after `reference_date` (default: today).

        Nothing is published if no venue could be read, so the previous edition stays online.
        """
        now = self._clock()
        window = self._window_for_date(reference_date or now.date())
        events, statuses = self._collect(window)
        program = self._selection.select(events, window)
        footer = FooterInfo(
            generated_at=now,
            healthy_venues=tuple(status.venue_name for status in statuses if status.is_healthy),
            failed_venues=tuple(status.venue_name for status in statuses if not status.is_healthy),
        )
        if not footer.healthy_venues:
            LOGGER.error("Keine einzige Quelle lieferte Daten – es wird nichts veröffentlicht.")
            return UpdateReport(program, tuple(statuses), ())
        calendar = self._renderer.render(program, footer)
        written = self._publisher.publish(calendar, program, footer, statuses)
        return UpdateReport(program, tuple(statuses), tuple(written))

    def _collect(self, window: WeekendWindow) -> tuple[list[Event], list[SourceStatus]]:
        events: list[Event] = []
        statuses: list[SourceStatus] = []
        for source in self._sources:
            try:
                found = source.fetch_events(window)
            except Exception as error:  # one broken website must never stop the whole edition
                LOGGER.warning("%s konnte nicht gelesen werden: %s", source.venue_name, error)
                statuses.append(SourceStatus(source.venue_name, error=f"{type(error).__name__}: {error}"))
                continue
            events.extend(found)
            statuses.append(SourceStatus(source.venue_name, event_count=len(found)))
        return events, statuses
