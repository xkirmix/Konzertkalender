"""Fixed header and footer geometry, shared by the layout planner and the renderer."""

from __future__ import annotations

from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.font_provider import FontProvider, FontRole

SUBTITLE_GAP = 6
RULE_THICKNESS = 5
GAP_BELOW_RULE = 22
GAP_ABOVE_FOOTER_TEXT = 12


class FrameGeometry:
    def __init__(self, theme: CalendarTheme, fonts: FontProvider) -> None:
        self._theme = theme
        self._fonts = fonts

    def title_line_height(self) -> int:
        return self._fonts.line_height(FontRole.HEAVY, self._theme.title_size, leading=1.0)

    def subtitle_line_height(self) -> int:
        return self._fonts.line_height(FontRole.SEMIBOLD, self._theme.subtitle_size)

    def rule_top(self) -> int:
        return self._theme.margin + self.title_line_height() + self.subtitle_line_height() + SUBTITLE_GAP

    def header_height(self) -> int:
        return self.rule_top() + RULE_THICKNESS + GAP_BELOW_RULE

    def footer_top(self) -> int:
        footer_text = self._fonts.line_height(FontRole.REGULAR, self._theme.footer_size)
        return self._theme.height - self._theme.margin - footer_text - GAP_ABOVE_FOOTER_TEXT

    def content_height(self) -> int:
        """Vertical space between header and footer available for the evenings."""
        return self.footer_top() - self.header_height()
