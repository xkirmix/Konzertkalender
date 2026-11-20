"""ISC Club Bern: program on the home page; exact start times only on the detail pages."""

from __future__ import annotations

import re
from datetime import date, time

from bs4.element import Tag

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.fetching.page_fetcher import PageFetchError
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

CANCELLED_PREFIX = re.compile(r"^\s*abgesagt\s*:?\s*", re.IGNORECASE)


class IscSource:
    venue_name = "ISC"
    program_url = "https://isc-club.ch/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card, window) for card in soup.select("a.event_preview"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag, window: WeekendWindow) -> Event | None:
        day = self._toolkit.dates.numeric_date(TextCleaner.text_of(card.select_one(".event_title_date")))
        raw_title = TextCleaner.text_of(card.select_one(".event_title_title"))
        if day is None or not raw_title:
            return None
        info = TextCleaner.text_of(card.select_one(".event_title_info"))
        kind_text, _, genre_text = info.partition(" - ")
        starts_at, has_time = self._toolkit.local_start(day, self._start_time(card.get("href"), window, day))
        return Event(
            venue=self.venue_name,
            title=CANCELLED_PREFIX.sub("", raw_title),
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_category_words(TextCleaner.split_list(kind_text, r"[,&/]"))
            or EventKind.CONCERT,
            genres=self._toolkit.genres.format_tags(TextCleaner.split_list(genre_text, r",")),
            url=card.get("href"),
            has_start_time=has_time,
            is_cancelled=bool(CANCELLED_PREFIX.match(raw_title)),
        )

    def _start_time(self, detail_url: str | None, window: WeekendWindow, day: date) -> time | None:
        """Reads the add-to-calendar start ("2026-11-27 20:00:00") of events in the window."""
        if not detail_url or not window.covers_day(day):
            return None
        try:
            detail = self._toolkit.soup(detail_url)
        except PageFetchError:
            return None
        parsed = self._toolkit.dates.iso_date_and_time(TextCleaner.text_of(detail.select_one("var.atc_date_start")))
        return parsed[1] if parsed else None
