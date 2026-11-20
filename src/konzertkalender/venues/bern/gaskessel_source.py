"""Gaskessel Bern: event previews with date, genre line and a doors time in an info table."""

from __future__ import annotations

from datetime import time
from urllib.parse import urljoin

from bs4.element import Tag

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

DOOR_LABELS = ("doors", "türöffnung", "tür", "beginn", "start")


class GaskesselSource:
    venue_name = "Gaskessel"
    program_url = "https://gaskessel.ch/programm/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card) for card in soup.select("article.eventpreview"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        day = self._toolkit.dates.numeric_date(TextCleaner.text_of(card.select_one(".eventdatum")))
        title = self._title(card.select_one(".eventname"))
        if day is None or not title:
            return None
        genre_line = TextCleaner.text_of(card.select_one(".eventgenre"))
        genres = self._toolkit.genres.format_tags(TextCleaner.split_list(genre_line, r","))
        starts_at, has_time = self._toolkit.local_start(day, self._door_time(card))
        link = card.select_one("[data-url]")
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_genres_and_title(genres, title, starts_at),
            genres=genres,
            url=urljoin(self.program_url, link["data-url"]) if link else None,
            has_start_time=has_time,
        )

    @staticmethod
    def _title(heading: Tag | None) -> str:
        """ "ULTRA DANCE w/ Lolalita <sup>BEL</sup>" -> "ULTRA DANCE w/ Lolalita (BEL)"."""
        if heading is None:
            return ""
        parts: list[str] = []
        for child in heading.children:
            is_tag = isinstance(child, Tag)
            text = TextCleaner.clean(child.get_text(" ") if is_tag else str(child))
            if text:
                parts.append(f"({text})" if is_tag and child.name == "sup" else text)
        return " ".join(parts)

    def _door_time(self, card: Tag) -> time | None:
        for row in card.select("div.trow"):
            cells = [TextCleaner.text_of(cell) for cell in row.select("div.tcell")]
            if len(cells) >= 2 and cells[0].lower() in DOOR_LABELS:
                return self._toolkit.dates.time_of_day(cells[1])
        return None
