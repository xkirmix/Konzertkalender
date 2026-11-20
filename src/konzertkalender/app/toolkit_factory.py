"""Builds the shared SourceToolkit from the configuration."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from konzertkalender.app.app_config import AppConfig
from konzertkalender.fetching.page_fetcher import HttpPageFetcher, PageFetcher
from konzertkalender.parsing.date_parsing import VenueDateParser
from konzertkalender.parsing.event_kind_classifier import EventKindClassifier
from konzertkalender.parsing.genre_normalizer import GenreNormalizer
from konzertkalender.parsing.genre_vocabulary import GenreVocabulary
from konzertkalender.venues.source_toolkit import SourceToolkit


class SourceToolkitFactory:
    @staticmethod
    def create(config: AppConfig, today: date, fetcher: PageFetcher | None = None) -> SourceToolkit:
        """`today` is the day the pages are read (for "Morgen" and missing years)."""
        genres = GenreNormalizer(GenreVocabulary.from_toml(config.genre_file))
        return SourceToolkit(
            fetcher=fetcher or HttpPageFetcher(),
            dates=VenueDateParser(today),
            genres=genres,
            kinds=EventKindClassifier(genres),
            timezone=ZoneInfo(config.timezone),
        )
