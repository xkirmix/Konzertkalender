"""Fixed frame geometry, shared by the layout planner and the renderer.

There is no header: the evening bars carry the dates, so all height above the footer belongs to the
events. The footer shows when the edition was made and which venues could be read.
"""

from __future__ import annotations

from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.font_provider import FontProvider
from konzertkalender.rendering.meta_fonts import MetaFonts

GAP_ABOVE_FOOTER_TEXT = 12


class FrameGeometry:
    def __init__(self, theme: CalendarTheme, fonts: FontProvider) -> None:
        self._theme = theme
        self._fonts = fonts

    def content_top(self) -> int:
        return self._theme.margin

    def footer_top(self) -> int:
        footer_text = MetaFonts(self._fonts).footer_line_height(self._theme.footer_size)
        return self._theme.height - self._theme.margin - footer_text - GAP_ABOVE_FOOTER_TEXT

    def content_height(self) -> int:
        """Vertical space above the footer available for the evenings."""
        return self.footer_top() - self.content_top()
