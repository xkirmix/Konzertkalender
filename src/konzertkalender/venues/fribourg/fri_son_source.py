"""Fri-Son (Fribourg): Drupal event teasers with performers, date, doors time and genres."""

from __future__ import annotations

from urllib.parse import urljoin

from bs4.element import Tag

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

CANCELLED_WORDS = ("abgesagt", "annule", "cancel", "verschoben", "reporte")


class FriSonSource:
    venue_name = "Fri-Son"
    program_url = "https://www.fri-son.ch/de/programm"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events = (self._parse_card(card) for card in soup.select("article.node--type-event"))
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        day = self._toolkit.dates.named_month_date(TextCleaner.text_of(card.select_one("time.datetime")))
        title = ", ".join(filter(None, (self._performer(item) for item in card.select(".performers.main .performer"))))
        if day is None or not title:
            return None
        doors = self._toolkit.dates.time_of_day(TextCleaner.text_of(card.select_one(".field--name-field-time-doors")))
        genres = self._toolkit.genres.format_tags(
            TextCleaner.text_of(item) for item in card.select(".genre-wrapper .field__item")
        )
        status = TextCleaner.fold(TextCleaner.text_of(card.select_one(".status-wrapper")))
        link = card.find("a", href=True)
        starts_at, has_time = self._toolkit.local_start(day, doors)
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_genres_and_title(genres, title, starts_at),
            genres=genres,
            url=urljoin(self.program_url, link["href"]) if link else None,
            has_start_time=has_time,
            is_cancelled=any(word in status for word in CANCELLED_WORDS),
        )

    @staticmethod
    def _performer(performer: Tag) -> str:
        """ "MARIA BC <sup>US</sup>" -> "MARIA BC (US)"."""
        name = TextCleaner.clean(" ".join(performer.find_all(string=True, recursive=False)))
        origin = TextCleaner.text_of(performer.find("sup"))
        return f"{name} ({origin})" if name and origin else name
