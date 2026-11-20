"""Small text helpers shared by all HTML parsers."""

from __future__ import annotations

import re
import unicodedata

from bs4.element import Tag

WHITESPACE = re.compile(r"\s+")
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "`": "'", "´": "'"})


class TextCleaner:
    """Normalizes whitespace and extracts readable text from BeautifulSoup elements."""

    @staticmethod
    def clean(text: str | None) -> str:
        return WHITESPACE.sub(" ", text or "").strip()

    @classmethod
    def text_of(cls, element: Tag | None, separator: str = " ") -> str:
        """Visible text of an element with collapsed whitespace; empty string for None."""
        return cls.clean(element.get_text(separator)) if element is not None else ""

    @staticmethod
    def fold(text: str | None) -> str:
        """Lowercase, accent-free form for matching: "Fête Électro" -> "fete electro"."""
        decomposed = unicodedata.normalize("NFKD", (text or "").translate(APOSTROPHES))
        return "".join(char for char in decomposed if not unicodedata.combining(char)).lower()

    @staticmethod
    def split_list(text: str | None, separators: str = r"[,/;]") -> list[str]:
        """Splits "Rock, Punk / Pop" style lists into trimmed, non-empty parts."""
        return [part.strip() for part in re.split(separators, text or "") if part.strip()]
