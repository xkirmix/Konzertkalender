"""Cafete (Reitschule Bern): one-page program with date, line-up and a "Style:" genre line."""

from __future__ import annotations

import re

from bs4.element import Tag

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

STYLE_PREFIX = re.compile(r"^\s*style\s*:\s*", re.IGNORECASE)


class CafeteSource:
    venue_name = "Cafete"
    program_url = "https://cafete.ch/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card) for card in soup.select("div.event"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        date_text = TextCleaner.text_of(card.select_one(".date"))  # "Fr. 20. November 2026 — 23:00"
        day = self._toolkit.dates.named_month_date(date_text)
        title = TextCleaner.text_of(card.select_one(".title"))
        if day is None or not title:
            return None
        style = STYLE_PREFIX.sub("", TextCleaner.text_of(card.select_one(".style")))
        genres = self._toolkit.genres.format_tags(TextCleaner.split_list(style, r"[/,]"))
        starts_at, has_time = self._toolkit.local_start(day, self._toolkit.dates.time_of_day(date_text))
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_genres_and_title(genres, title, starts_at),
            genres=genres,
            url=self.program_url,
            has_start_time=has_time,
        )
