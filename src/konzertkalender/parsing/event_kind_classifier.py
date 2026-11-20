"""Deciding whether an event is a concert, a party/DJ night or something else."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from datetime import datetime

from konzertkalender.domain.event import EventKind
from konzertkalender.parsing.genre_normalizer import GenreNormalizer
from konzertkalender.parsing.text_cleaning import TextCleaner

CONCERT_WORDS = frozenset({"konzert", "konzerte", "concert", "concerts", "live", "musik", "volksmusik", "crt"})
PARTY_WORDS = frozenset({
    "party", "partys", "clubnight", "club", "clubbing", "dj", "djs", "dj-set", "dj-sets", "djset",
    "disco", "rave", "fte", "fete",
})
NON_MUSIC_HINTS = (
    "quiz", "workshop", "lesung", "literatur", "flohmarkt", "markt", "brunch", "kino", "film",
    "vortrag", "podium", "fuhrung", "yoga", "spielabend", "atelier", "cafe scientifique", "schach",
)
PARTY_TITLE_PATTERN = re.compile(r"\b(?:dj|djs|dj-set|party|rave|club ?night|disco|b2b)\b|\bw/")
CONCERT_TITLE_PATTERN = re.compile(
    r"\b(?:support|live|konzert|concert|band|tour|plattentaufe|album|release|vernissage|unplugged|acoustic)\b"
)
CATEGORY_WORD = re.compile(r"[a-z0-9]+(?:-[a-z]+)?")
LATE_PARTY_HOUR = 23
NIGHT_END_HOUR = 5


class EventKindClassifier:
    """Maps venue categories, genres, title hints and start times to an EventKind."""

    def __init__(self, genres: GenreNormalizer) -> None:
        self._genres = genres

    def from_category_words(self, categories: Iterable[str]) -> EventKind | None:
        """Proper categories ("Konzert", "Clubnight, Party", "Theater"); None if there are none."""
        words = self._category_words(categories)
        if not words:
            return None
        if words & CONCERT_WORDS:
            return EventKind.CONCERT
        if words & PARTY_WORDS or any(word.endswith("party") for word in words):
            return EventKind.PARTY
        return EventKind.OTHER

    def from_tags(self, tags: Iterable[str], genres: Sequence[str], title: str, starts_at: datetime) -> EventKind:
        """Mixed tag lists (kind words, genres, labels): kind words win, otherwise the genres decide."""
        tag_kind = self.from_category_words(tags)
        if tag_kind in (EventKind.CONCERT, EventKind.PARTY):
            return tag_kind
        return self.from_genres_and_title(genres, title, starts_at) if genres else EventKind.OTHER

    def from_genres_and_title(self, genres: Sequence[str], title: str, starts_at: datetime) -> EventKind:
        """For venues without categories, in order: non-music hints, dance genres, late start,
        concert words in the title ("Support", "Tour" ...), DJ/party words in the title."""
        folded_title = TextCleaner.fold(title)
        if self._looks_non_musical(folded_title, genres):
            return EventKind.OTHER
        if any(self._genres.is_dance(genre) for genre in genres):
            return EventKind.PARTY
        if starts_at.hour >= LATE_PARTY_HOUR or starts_at.hour < NIGHT_END_HOUR:
            return EventKind.PARTY
        if CONCERT_TITLE_PATTERN.search(folded_title):
            return EventKind.CONCERT
        return EventKind.PARTY if PARTY_TITLE_PATTERN.search(folded_title) else EventKind.CONCERT

    def _looks_non_musical(self, folded_title: str, genres: Sequence[str]) -> bool:
        """A quiz or workshop: a non-music hint and no genre the vocabulary knows."""
        if any(self._genres.is_known_genre(genre) for genre in genres):
            return False
        searchable = " ".join([folded_title, *(TextCleaner.fold(genre) for genre in genres)])
        return any(hint in searchable for hint in NON_MUSIC_HINTS)

    @staticmethod
    def _category_words(categories: Iterable[str]) -> set[str]:
        words: set[str] = set()
        for category in categories:
            words.update(CATEGORY_WORD.findall(TextCleaner.fold(category)))
        return words
