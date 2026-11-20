"""Shortening and wrapping text so it fits a given pixel width."""

from __future__ import annotations

from PIL import ImageFont

ELLIPSIS = "…"
TRAILING_PUNCTUATION = " ,;:–-·/"


class TextFitter:
    @staticmethod
    def width(text: str, font: ImageFont.FreeTypeFont) -> float:
        return font.getlength(text)

    def ellipsize(self, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
        """The longest prefix that fits, ending in an ellipsis (binary search over characters)."""
        if self.width(text, font) <= max_width:
            return text
        shortest, longest = 0, len(text)
        while shortest < longest:
            middle = (shortest + longest + 1) // 2
            if self.width(text[:middle].rstrip() + ELLIPSIS, font) <= max_width:
                shortest = middle
            else:
                longest = middle - 1
        return text[:shortest].rstrip(TRAILING_PUNCTUATION) + ELLIPSIS

    def wrap(self, text: str, font: ImageFont.FreeTypeFont, max_width: float, max_lines: int) -> list[str]:
        """Word wrap into at most `max_lines` lines; the last line is ellipsized if needed."""
        if max_lines <= 1:
            return [self.ellipsize(text, font, max_width)]
        words = text.split()
        lines: list[str] = []
        current = ""
        for index, word in enumerate(words):
            candidate = f"{current} {word}".strip()
            if self.width(candidate, font) <= max_width or not current:
                current = candidate
                continue
            lines.append(current)
            if len(lines) == max_lines - 1:
                remainder = " ".join(words[index:])
                return [*lines, self.ellipsize(remainder, font, max_width)]
            current = word
        if current:
            lines.append(self.ellipsize(current, font, max_width))
        return lines[:max_lines]
