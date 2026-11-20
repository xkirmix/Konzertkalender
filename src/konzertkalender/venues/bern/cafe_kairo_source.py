"""Café Kairo (Bern Lorraine): program blocks with a category; genres come from the description."""

from __future__ import annotations

from bs4.element import Tag

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

START_LABELS = ("start", "beginn", "konzert")


class CafeKairoSource:
    venue_name = "Café Kairo"
    program_url = "https://www.cafe-kairo.ch/programm"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card) for card in soup.select("article.content_block"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        stamp = card.select_one("time[datetime]")
        parsed = self._toolkit.dates.iso_date_and_time(stamp.get("datetime", "")) if stamp else None
        title = TextCleaner.text_of(card.select_one("h2"))
        if parsed is None or not title:
            return None
        day, listed_time = parsed
        schedule = TextCleaner.text_of(stamp.find_parent("p"))  # "Tür 19:30, Start 20:00 Fr. 20.11.2026"
        start = self._toolkit.dates.labeled_time(schedule, START_LABELS) or listed_time
        category = TextCleaner.text_of(card.select_one("p.uppercase"))
        starts_at, has_time = self._toolkit.local_start(day, start)
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_category_words([category]) or EventKind.CONCERT,
            genres=self._toolkit.genres.genres_from_text(TextCleaner.text_of(card.select_one("div.text"))),
            url=self.program_url,
            has_start_time=has_time,
        )
