"""PROGR (Bern): agenda of the whole cultural centre; only music categories are kept later."""

from __future__ import annotations

from datetime import date
from urllib.parse import urljoin

from bs4.element import Tag

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit


class ProgrSource:
    venue_name = "PROGR"
    program_url = "https://www.progr.ch/de/agenda/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card) for card in soup.select("article.event"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        heading = card.select_one("div.title h2")
        if heading is None:
            return None
        date_label = heading.select_one(".invisible")  # "Fr. 20.11."
        day = self._day(card, date_label)
        words = [TextCleaner.text_of(span) for span in heading.find_all("span", recursive=False) if span is not date_label]
        title = TextCleaner.clean(" ".join(words))
        if day is None or not title:
            return None
        categories = TextCleaner.split_list(TextCleaner.text_of(card.select_one("span.categories")), r",")
        clock = self._toolkit.dates.time_of_day(TextCleaner.text_of(card.select_one("div.time")))
        starts_at, has_time = self._toolkit.local_start(day, clock)
        detail_path = card.get("data-g-path")
        return Event(
            venue=self._venue_label(TextCleaner.text_of(card.select_one("span.venues"))),
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_category_words(categories) or EventKind.OTHER,
            genres=self._toolkit.genres.genres_from_text(TextCleaner.text_of(card.select_one("div.text"))),
            url=urljoin(self.program_url, detail_path) if detail_path else self.program_url,
            has_start_time=has_time,
        )

    def _day(self, card: Tag, date_label: Tag | None) -> date | None:
        """Prefers the exact data-g-date attribute ("2026-11-20") over the visible "Fr. 20.11."."""
        parsed = self._toolkit.dates.iso_date_and_time(card.get("data-g-date", ""))
        return parsed[0] if parsed else self._toolkit.dates.numeric_date(TextCleaner.text_of(date_label))

    def _venue_label(self, room: str) -> str:
        """ "PROGR Turnhalle" stays, partner stages become "bee-flat (PROGR)"."""
        if not room or room.upper().startswith(self.venue_name):
            return room or self.venue_name
        return f"{room} ({self.venue_name})"
