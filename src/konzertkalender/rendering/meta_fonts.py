"""The fonts of the venue/genre line and the footer, shared by layout measuring and drawing.

Thin weights look washed out on e-ink, so the smaller texts use bold and semibold Inter.
"""

from __future__ import annotations

from PIL import ImageFont

from konzertkalender.rendering.font_provider import FontProvider, FontRole

VENUE_ROLE = FontRole.BOLD
DETAILS_ROLE = FontRole.SEMIBOLD
FOOTER_ROLE = FontRole.SEMIBOLD


class MetaFonts:
    def __init__(self, fonts: FontProvider) -> None:
        self._fonts = fonts

    def venue(self, size: int) -> ImageFont.FreeTypeFont:
        return self._fonts.get(VENUE_ROLE, size)

    def details(self, size: int) -> ImageFont.FreeTypeFont:
        return self._fonts.get(DETAILS_ROLE, size)

    def footer(self, size: int) -> ImageFont.FreeTypeFont:
        return self._fonts.get(FOOTER_ROLE, size)

    def details_line_height(self, size: int) -> int:
        return self._fonts.line_height(DETAILS_ROLE, size, leading=1.12)

    def footer_line_height(self, size: int) -> int:
        return self._fonts.line_height(FOOTER_ROLE, size)
