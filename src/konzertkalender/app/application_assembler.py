"""Composition root: wires configuration, venue sources, rendering and publishing together."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

from konzertkalender.app.app_config import AppConfig
from konzertkalender.app.toolkit_factory import SourceToolkitFactory
from konzertkalender.app.weekly_update_coordinator import WeeklyUpdateCoordinator
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.fetching.page_fetcher import PageFetcher
from konzertkalender.publishing.calendar_page_builder import CalendarPageBuilder
from konzertkalender.publishing.event_list_page_builder import EventListPageBuilder
from konzertkalender.publishing.program_serializer import ProgramSerializer
from konzertkalender.publishing.site_publisher import SitePublisher
from konzertkalender.rendering.calendar_layout import CalendarLayoutPlanner
from konzertkalender.rendering.calendar_renderer import KindleCalendarRenderer
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider
from konzertkalender.rendering.text_fitter import TextFitter
from konzertkalender.selection.event_selection_manager import EventSelectionManager
from konzertkalender.venues.venue_registry import VenueRegistry

FOOTER_HINT = "Details: Kindle aufwecken"


class ApplicationAssembler:
    def __init__(
        self,
        config: AppConfig,
        output_dir: Path,
        clock: Callable[[], datetime],
        fetcher: PageFetcher | None = None,
        theme: CalendarTheme | None = None,
    ) -> None:
        self._config = config
        self._output_dir = output_dir
        self._clock = clock
        self._fetcher = fetcher
        self._theme = theme or CalendarTheme()

    def build_coordinator(self) -> WeeklyUpdateCoordinator:
        config = self._config
        toolkit = SourceToolkitFactory.create(config, today=self._clock().date(), fetcher=self._fetcher)
        formatter = EventTextFormatter()
        return WeeklyUpdateCoordinator(
            sources=VenueRegistry().build(config.venue_keys, toolkit),
            selection=EventSelectionManager(config.included_kinds),
            renderer=self._build_renderer(formatter),
            publisher=SitePublisher(
                self._output_dir,
                CalendarPageBuilder(config.title, formatter),
                EventListPageBuilder(config.title, formatter),
                ProgramSerializer(),
            ),
            clock=self._clock,
            window_for_date=self._window_for_date,
        )

    def _build_renderer(self, formatter: EventTextFormatter) -> KindleCalendarRenderer:
        fonts = FontProvider(self._theme.fonts)
        fitter = TextFitter()
        planner = CalendarLayoutPlanner(self._theme, fonts, fitter, formatter)
        return KindleCalendarRenderer(
            self._theme, fonts, planner, fitter, FOOTER_HINT
        )

    def _window_for_date(self, reference: date) -> WeekendWindow:
        return WeekendWindow.for_reference_date(
            reference, self._config.evening_start_hour, self._config.night_end_hour
        )
