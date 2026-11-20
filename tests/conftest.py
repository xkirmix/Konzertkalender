"""Shared test helpers: an offline page fetcher, fixtures and a toolkit factory."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.fetching.page_fetcher import PageFetchError
from konzertkalender.parsing.date_parsing import VenueDateParser
from konzertkalender.parsing.event_kind_classifier import EventKindClassifier
from konzertkalender.parsing.genre_normalizer import GenreNormalizer
from konzertkalender.parsing.genre_vocabulary import GenreVocabulary
from konzertkalender.venues.source_toolkit import SourceToolkit

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TODAY = date(2026, 11, 20)  # a Friday: the day the pages were "read"
NEXT_MONDAY = date(2026, 11, 23)  # the weekly run -> weekend Thu 26 - Sat 28 Nov 2026
ZURICH = ZoneInfo("Europe/Zurich")


class FakePageFetcher:
    """Serves fixture HTML by URL and records which URLs were requested."""

    def __init__(self, pages: dict[str, str]) -> None:
        self.pages = pages
        self.requested: list[str] = []

    def fetch_text(self, url: str) -> str:
        self.requested.append(url)
        if url not in self.pages:
            raise PageFetchError(f"{url}: nicht in den Testdaten")
        return self.pages[url]


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def genre_normalizer() -> GenreNormalizer:
    return GenreNormalizer(GenreVocabulary.from_toml(PROJECT_ROOT / "config" / "genres.toml"))


@pytest.fixture
def weekend() -> WeekendWindow:
    return WeekendWindow.for_reference_date(NEXT_MONDAY)


@pytest.fixture
def make_toolkit(genre_normalizer: GenreNormalizer) -> Callable[[dict[str, str]], tuple[FakePageFetcher, SourceToolkit]]:
    def factory(pages: dict[str, str]) -> tuple[FakePageFetcher, SourceToolkit]:
        fetcher = FakePageFetcher(pages)
        toolkit = SourceToolkit(
            fetcher=fetcher,
            dates=VenueDateParser(TODAY),
            genres=genre_normalizer,
            kinds=EventKindClassifier(genre_normalizer),
            timezone=ZURICH,
        )
        return fetcher, toolkit

    return factory
