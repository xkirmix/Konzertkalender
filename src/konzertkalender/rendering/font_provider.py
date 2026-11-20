"""Loads and caches the calendar fonts by role and pixel size."""

from __future__ import annotations

from enum import Enum

from PIL import ImageFont

from konzertkalender.rendering.calendar_theme import FontFiles


class FontRole(Enum):
    REGULAR = "regular"
    SEMIBOLD = "semibold"
    BOLD = "bold"
    HEAVY = "heavy"


class FontProvider:
    def __init__(self, files: FontFiles) -> None:
        self._paths = {
            FontRole.REGULAR: files.regular,
            FontRole.SEMIBOLD: files.semibold,
            FontRole.BOLD: files.bold,
            FontRole.HEAVY: files.heavy,
        }
        self._cache: dict[tuple[FontRole, int], ImageFont.FreeTypeFont] = {}

    def get(self, role: FontRole, size: int) -> ImageFont.FreeTypeFont:
        key = (role, size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(str(self._paths[role]), size)
        return self._cache[key]

    def line_height(self, role: FontRole, size: int, leading: float = 1.12) -> int:
        ascent, descent = self.get(role, size).getmetrics()
        return round((ascent + descent) * leading)
