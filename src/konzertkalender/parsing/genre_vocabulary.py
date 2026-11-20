"""Recognizing music genres in venue tag lists and in free description text.

The vocabulary is configured in config/genres.toml so new genres can be added without code.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from konzertkalender.parsing.text_cleaning import TextCleaner

MAX_TAG_WORDS = 3
WORD_PATTERN = re.compile(r"[a-z0-9'&]+(?:-[a-z0-9'&]+)*")
PHRASE_JOINS = (
    (re.compile(r"hip[\s-]*hop"), "hiphop"),
    (re.compile(r"drum\s*(?:and|&|'?n'?)\s*bass"), "drumandbass"),
    (re.compile(r"rock\s*'?\s*n\s*'?\s*roll"), "rocknroll"),
    (re.compile(r"\br\s*&\s*b\b|\br'n'b\b"), "rnb"),
    (re.compile(r"singer[\s/-]*songwriter"), "songwriter"),
    (re.compile(r"trip[\s-]*hop"), "triphop"),
    (re.compile(r"\blo[\s-]*fi\b"), "lofi"),
    (re.compile(r"post[\s-]*punk"), "postpunk"),
    (re.compile(r"post[\s-]*rock"), "postrock"),
    (re.compile(r"punk[\s-]*rock"), "punkrock"),
    (re.compile(r"new[\s-]*wave"), "newwave"),
    (re.compile(r"big[\s-]*band"), "bigband"),
    (re.compile(r"hard[\s-]*dance"), "harddance"),
)


class MatchMode(Enum):
    WORD = "word"
    SUFFIX = "suffix"
    PREFIX = "prefix"
    CONTAINS = "contains"


@dataclass(frozen=True)
class GenreTerm:
    """One genre with the word stems that identify it."""

    name: str
    stems: tuple[str, ...]
    mode: MatchMode
    dance: bool = False
    tag_only: bool = False
    excluded_words: tuple[str, ...] = ()

    @classmethod
    def from_config(cls, key: str, settings: dict[str, Any]) -> "GenreTerm":
        return cls(
            name=settings.get("name", key),
            stems=tuple(TextCleaner.fold(stem) for stem in settings["stems"]),
            mode=MatchMode(settings.get("mode", "word")),
            dance=bool(settings.get("dance", False)),
            tag_only=bool(settings.get("tag_only", False)),
            excluded_words=tuple(TextCleaner.fold(word) for word in settings.get("exclude", ())),
        )

    def matches(self, word: str) -> bool:
        if word in self.excluded_words:
            return False
        return any(self._matches_stem(word, stem) for stem in self.stems)

    def _matches_stem(self, word: str, stem: str) -> bool:
        if self.mode is MatchMode.WORD:
            return word in (stem, stem + "s")
        if self.mode is MatchMode.SUFFIX:
            return word.endswith(stem)
        if self.mode is MatchMode.PREFIX:
            return word.startswith(stem)
        return stem in word


class GenreVocabulary:
    """Ordered list of genre terms; the first matching term wins."""

    def __init__(self, terms: Iterable[GenreTerm]) -> None:
        self._terms = tuple(terms)

    @classmethod
    def from_toml(cls, path: Path) -> "GenreVocabulary":
        with path.open("rb") as handle:
            configured = tomllib.load(handle)["genres"]
        return cls(GenreTerm.from_config(key, settings) for key, settings in configured.items())

    def term_for_tag(self, tag: str) -> GenreTerm | None:
        """The genre a short tag like "Post Punk" or "Vintage Indo-Pop" stands for, if any."""
        words = self._words(tag)
        if not words or len(words) > MAX_TAG_WORDS:
            return None
        for candidate in self._candidates(words[-1]):
            term = self._first_match(candidate, include_tag_only=True)
            if term is not None:
                return term
        return None

    def find_in_text(self, text: str, limit: int) -> list[str]:
        """Genre names mentioned in prose, in order of first mention."""
        found: list[str] = []
        for word in self._words(text):
            for candidate in self._candidates(word):
                term = self._first_match(candidate, include_tag_only=False)
                if term is not None and term.name not in found:
                    found.append(term.name)
                    if len(found) >= limit:
                        return found
        return found

    def is_dance(self, genre: str) -> bool:
        term = self.term_for_tag(genre)
        return bool(term and term.dance)

    def _first_match(self, word: str, include_tag_only: bool) -> GenreTerm | None:
        for term in self._terms:
            if (include_tag_only or not term.tag_only) and term.matches(word):
                return term
        return None

    @staticmethod
    def _words(text: str) -> list[str]:
        folded = TextCleaner.fold(text)
        for pattern, replacement in PHRASE_JOINS:
            folded = pattern.sub(replacement, folded)
        return WORD_PATTERN.findall(folded)

    @staticmethod
    def _candidates(word: str) -> list[str]:
        """The word itself, without hyphens, plus its hyphen-separated parts."""
        parts = [part.strip("'&") for part in word.split("-")]
        joined = "".join(parts)
        return [joined] + [part for part in parts if part and part != joined]
