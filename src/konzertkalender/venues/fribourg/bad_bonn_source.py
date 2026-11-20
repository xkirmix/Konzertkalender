"""Bad Bonn (Düdingen): compact program rows; genres are read from the detail descriptions."""

from __future__ import annotations

import re
from datetime import date

from bs4.element import Tag

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.text_cleaning import TextCleaner
from konzertkalender.venues.source_toolkit import SourceToolkit

YEAR_IN_URL = re.compile(r"/archive/(\d{4})/")
DJ_SET_LABEL = "dj-set"


class BadBonnSource:
    venue_name = "Bad Bonn"
    program_url = "https://club.badbonn.ch/"

    def __init__(self, toolkit: SourceToolkit) -> None:
        self._toolkit = toolkit

    def fetch_events(self, window: WeekendWindow) -> list[Event]:
        soup = self._toolkit.soup(self.program_url)
        events: list[Event] = []
        month: int | None = None
        for row in soup.select("a[href*='/archive/']"):
            cells = row.find_all("div", recursive=False)
            month = self._month_of(cells) or month  # the month is only printed on its first row
            event = self._parse_row(row, cells, month, window)
            if event is not None:
                events.append(event)
        return events

    def _parse_row(self, row: Tag, cells: list[Tag], month: int | None, window: WeekendWindow) -> Event | None:
        """Row cells: month (only on the first row of a month), day, time, title (+ "DJ-Set")."""
        day = self._day(row.get("href", ""), cells, month)
        title = TextCleaner.text_of(row.select_one("h1"))
        if day is None or not title:
            return None
        detail_text = self._toolkit.page_text_or_empty(row.get("href")) if window.covers_day(day) else ""
        genres = self._toolkit.genres.genres_from_text(detail_text)
        is_dj_set = any(DJ_SET_LABEL in TextCleaner.fold(TextCleaner.text_of(cell)) for cell in cells[3:])
        starts_at, has_time = self._toolkit.local_start(day, self._toolkit.dates.time_of_day(TextCleaner.text_of(cells[2])))
        return Event(
            venue=self.venue_name,
            title=title,
            starts_at=starts_at,
            kind=EventKind.PARTY if is_dj_set else self._toolkit.kinds.from_genres_and_title(genres, title, starts_at),
            genres=genres,
            url=row.get("href"),
            has_start_time=has_time,
        )

    def _month_of(self, cells: list[Tag]) -> int | None:
        return self._toolkit.dates.month_number(TextCleaner.text_of(cells[0])) if cells else None

    @staticmethod
    def _day(url: str, cells: list[Tag], month: int | None) -> date | None:
        year = YEAR_IN_URL.search(url)
        day_text = TextCleaner.text_of(cells[1]) if len(cells) > 2 else ""
        if month is None or year is None or not day_text.isdigit():
            return None
        try:
            return date(int(year.group(1)), month, int(day_text))
        except ValueError:
            return None
