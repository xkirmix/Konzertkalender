"""Shared, injected helpers for venue sources (composition instead of a base class)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from konzertkalender.fetching.page_fetcher import PageFetcher, PageFetchError
from konzertkalender.parsing.date_parsing import VenueDateParser
from konzertkalender.parsing.event_kind_classifier import EventKindClassifier
from konzertkalender.parsing.genre_normalizer import GenreNormalizer
from konzertkalender.parsing.text_cleaning import TextCleaner

DEFAULT_START = time(20, 0)


@dataclass(frozen=True)
class SourceToolkit:
    fetcher: PageFetcher
    dates: VenueDateParser
    genres: GenreNormalizer
    kinds: EventKindClassifier
    timezone: ZoneInfo

    def soup(self, url: str) -> BeautifulSoup:
        return BeautifulSoup(self.fetcher.fetch_text(url), "html.parser")

    def local_start(self, day: date, start: time | None) -> tuple[datetime, bool]:
        """Local start datetime; unknown times fall back to 20:00 and are flagged as unknown."""
        return datetime.combine(day, start or DEFAULT_START, tzinfo=self.timezone), start is not None

    def page_text_or_empty(self, url: str | None) -> str:
        """Visible text of a detail page; empty if it cannot be loaded (details are optional)."""
        if not url:
            return ""
        try:
            return TextCleaner.text_of(self.soup(url).body)
        except PageFetchError:
            return ""
