"""Le Nouveau Monde (Fribourg): agenda posters with a category code (crt, fte, ...) and "20h30" times."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4.element import Tag

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

CATEGORY_KINDS = {"crt": EventKind.CONCERT, "fte": EventKind.PARTY, "clb": EventKind.PARTY}


class NouveauMondeSource:
    venue_name = "Nouveau Monde"
    program_url = "https://www.nouveaumonde.ch/agenda/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card, window) for card in soup.select("a.poster"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag, window: WeekendWindow) -> Event | None:
        date_text = TextCleaner.text_of(card.select_one("h3.date"))  # "27.11.2026", "Morgen", "Heute"
        day = self._toolkit.dates.numeric_date(date_text) or self._toolkit.dates.relative_day(date_text)
        title = TextCleaner.text_of(card.select_one("h4:not(.dateHM)"))
        if day is None or not title:
            return None
        url = urljoin(self.program_url, card.get("href", ""))
        genres = self._toolkit.genres.genres_from_text(title)
        if not genres and window.covers_day(day):
            genres = self._toolkit.genres.genres_from_text(self._toolkit.page_text_or_empty(url))
        clock = self._toolkit.dates.time_of_day(TextCleaner.text_of(card.select_one("h4.dateHM")))
        starts_at, has_time = self._toolkit.local_start(day, clock)
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=CATEGORY_KINDS.get(TextCleaner.fold(TextCleaner.text_of(card.select_one("li.plate"))), EventKind.OTHER),
            genres=genres,
            url=url,
            has_start_time=has_time,
        )
