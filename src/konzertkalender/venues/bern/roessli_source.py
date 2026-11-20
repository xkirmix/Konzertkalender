"""Rössli (Reitschule Bern): event cards with a datetime attribute and a mixed tag list."""

from __future__ import annotations

from bs4.element import Tag

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit


class RoessliSource:
    venue_name = "Rössli"
    program_url = "https://www.souslepont-roessli.ch/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        cards = [link for link in soup.select("a[href]") if link.select_one("time.event-date")]
        events = (self._parse_card(card) for card in cards)
        return [event for event in events if event is not None]

    def _parse_card(self, card: Tag) -> Event | None:
        stamp_element = card.select_one("time.event-date")
        stamp = stamp_element.get("datetime") or TextCleaner.text_of(stamp_element)  # "So., 22. Nov. 2026 20:00 - 23:30"
        day = self._toolkit.dates.named_month_date(stamp)
        title = TextCleaner.text_of(card.select_one("h2"))
        if day is None or not title:
            return None
        tags = [TextCleaner.text_of(item) for item in card.select("ul.event-categories li")]
        genres = self._toolkit.genres.select_genre_tags(tags)
        starts_at, has_time = self._toolkit.local_start(day, self._toolkit.dates.time_of_day(stamp))
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=self._toolkit.kinds.from_tags(tags, genres, title, starts_at),
            genres=genres,
            url=card.get("href"),
            has_start_time=has_time,
        )
