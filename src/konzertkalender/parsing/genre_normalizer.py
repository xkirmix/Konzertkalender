"""Turning raw venue tags and descriptions into a short, clean list of genres for display."""

from __future__ import annotations

import re
from collections.abc import Iterable

from konzertkalender.parsing.genre_vocabulary import GenreVocabulary
from konzertkalender.parsing.text_cleaning import TextCleaner

KIND_ONLY_TAGS = frozenset({
    "konzert", "konzerte", "concert", "concerts", "party", "partys", "clubnight", "clubbing",
    "dj", "djs", "dj-set", "dj-sets", "djset", "live",
})
WORD_TO_CAPITALIZE = re.compile(r"[^\W\d_][\w']*")
SHORT_ACRONYM_LENGTH = 4


class GenreNormalizer:
    """Cleans, formats, de-duplicates and limits genre lists."""

    def __init__(self, vocabulary: GenreVocabulary, max_genres: int = 3) -> None:
        self._vocabulary = vocabulary
        self._max_genres = max_genres

    def format_tags(self, raw_tags: Iterable[str]) -> tuple[str, ...]:
        """For fields a venue fills with genres only (e.g. "Garage Rock, Trash Punk")."""
        return self._limited(self._format(tag) for tag in self._without_kind_words(raw_tags))

    def select_genre_tags(self, raw_tags: Iterable[str], fallback_to_raw: bool = False) -> tuple[str, ...]:
        """For mixed tag lists (genres plus labels, series names ...): keep recognized genres only."""
        tags = list(self._without_kind_words(raw_tags))
        recognized = [tag for tag in tags if self._vocabulary.term_for_tag(tag) is not None]
        chosen = recognized or (tags[:2] if fallback_to_raw else [])
        return self._limited(self._format(tag) for tag in chosen)

    def genres_from_text(self, text: str) -> tuple[str, ...]:
        """Genres mentioned in a description text (canonical names)."""
        return tuple(self._vocabulary.find_in_text(text, self._max_genres))

    def is_dance(self, genre: str) -> bool:
        return self._vocabulary.is_dance(genre)

    def is_known_genre(self, genre: str) -> bool:
        return self._vocabulary.term_for_tag(genre) is not None

    def _limited(self, genres: Iterable[str]) -> tuple[str, ...]:
        unique: list[str] = []
        for genre in genres:
            if genre and genre.lower() not in (known.lower() for known in unique):
                unique.append(genre)
        return tuple(unique[: self._max_genres])

    @staticmethod
    def _without_kind_words(raw_tags: Iterable[str]) -> Iterable[str]:
        for tag in raw_tags:
            folded = TextCleaner.fold(tag).strip()
            if folded and folded not in KIND_ONLY_TAGS and not folded.endswith("party"):
                yield tag

    @staticmethod
    def _format(tag: str) -> str:
        """ "SYNTHPOP" -> "Synthpop", "TRASH-PUNK" -> "Trash-Punk"; short acronyms like EBM stay."""
        cleaned = TextCleaner.clean(tag).strip(" -–·")
        if cleaned.isupper() and len(cleaned) > SHORT_ACRONYM_LENGTH:
            return WORD_TO_CAPITALIZE.sub(lambda match: match.group(0).capitalize(), cleaned)
        return cleaned
