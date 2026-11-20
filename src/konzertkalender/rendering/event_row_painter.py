"""Draws one event row: club name (first row of a club), title, room/kind/genres and start time.

Club, first title line and time share one baseline, so the columns line up across rows.
"""

from __future__ import annotations

from PIL import ImageDraw

from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_row_builder import EventRow, RowStyle
from konzertkalender.rendering.font_provider import FontProvider, FontRole
from konzertkalender.rendering.layout_metrics import ScaledMetrics
from konzertkalender.rendering.meta_fonts import MetaFonts


class EventRowPainter:
    def __init__(self, theme: CalendarTheme, fonts: FontProvider) -> None:
        self._theme = theme
        self._fonts = fonts
        self._meta_fonts = MetaFonts(fonts)

    def paint(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics, top: int) -> int:
        """Draws the row starting at `top` and returns where the next row starts."""
        baseline = top + metrics.title_ascent
        self._paint_club_and_time(draw, row, metrics, baseline)
        if row.style is RowStyle.INLINE:
            self._paint_inline_text(draw, row, metrics, baseline)
        else:
            self._paint_stacked_text(draw, row, metrics, top, baseline)
        return top + row.height(metrics)

    def paint_separator(self, draw: ImageDraw.ImageDraw, y: float) -> None:
        """The hairline between two clubs of the same evening."""
        theme = self._theme
        draw.line((theme.margin, y, theme.width - theme.margin, y), fill=theme.separator_ink,
                  width=theme.separator_width)

    def text_x(self, metrics: ScaledMetrics) -> int:
        return self._theme.margin + metrics.club_column_width

    def _paint_club_and_time(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics,
                             baseline: int) -> None:
        theme = self._theme
        if row.club_label:
            draw.text((theme.margin, baseline), row.club_label, font=self._meta_fonts.club(metrics.meta_size),
                      fill=theme.club_ink, anchor="ls")
        draw.text((theme.width - theme.margin, baseline), row.time_label,
                  font=self._meta_fonts.time(metrics.time_size), fill=theme.ink, anchor="rs")

    def _paint_inline_text(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics,
                           baseline: int) -> None:
        x = self.text_x(metrics)
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        draw.text((x, baseline), row.title_lines[0], font=title_font, fill=self._theme.ink, anchor="ls")
        if row.details_label:
            draw.text((x + row.details_x_offset, baseline), row.details_label,
                      font=self._meta_fonts.details(metrics.meta_size), fill=self._theme.details_ink, anchor="ls")

    def _paint_stacked_text(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics, top: int,
                            baseline: int) -> None:
        x = self.text_x(metrics)
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        for index, line in enumerate(row.title_lines):
            draw.text((x, baseline + index * metrics.title_line_height), line, font=title_font,
                      fill=self._theme.ink, anchor="ls")
        details_top = top + len(row.title_lines) * metrics.title_line_height
        draw.text((x, details_top), row.details_label, font=self._meta_fonts.details(metrics.meta_size),
                  fill=self._theme.details_ink, anchor="la")
