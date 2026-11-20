"""Dachstock (Reitschule Bern): schema.org MusicEvent data embedded in the events page."""

from __future__ import annotations

from typing import Any

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.jsonld_event_reader import JsonLdEventReader
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit


class DachstockSource:
    venue_name = "Dachstock"
    program_url = "https://www.dachstock.ch/events"

    def __init__(self, toolkit: SourceToolkit, reader: JsonLdEventReader | None = None) -> None:
        self._toolkit = toolkit
        self._reader = reader or JsonLdEventReader()

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        html = self._toolkit.fetcher.fetch_text(self.program_url)
        events = (self._to_event(raw) for raw in self._reader.read_events(html))
        return [event for event in events if event is not None]

    def _to_event(self, raw: dict[str, Any]) -> Event | None:
        starts_at = self._toolkit.dates.aware_datetime(raw.get("startDate"))
        title = TextCleaner.clean(raw.get("name"))
        if starts_at is None or not title:
            return None
        tags = self._tags(raw.get("genre"))
        genres = self._toolkit.genres.select_genre_tags(tags)
        local_start = starts_at.astimezone(self._toolkit.timezone)
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=local_start,
            kind=self._toolkit.kinds.from_tags(tags, genres, title, local_start),
            genres=genres,
            url=raw.get("url"),
            is_cancelled="cancelled" in str(raw.get("eventStatus", "")).lower(),
        )

    @staticmethod
    def _tags(genre_field: Any) -> list[str]:
        """The first tag is the kind ("Konzert", "Party"), the rest are genres and fun tags."""
        if isinstance(genre_field, str):
            return [genre_field]
        return [str(tag) for tag in genre_field or []]
