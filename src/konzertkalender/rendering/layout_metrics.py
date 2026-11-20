"""All pixel sizes of the event list at one text scale."""

from __future__ import annotations

from dataclasses import dataclass

from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.font_provider import FontProvider, FontRole


@dataclass(frozen=True)
class ScaledMetrics:
    scale: float
    heading_size: int
    time_size: int
    event_title_size: int
    meta_size: int
    title_ascent: int
    title_line_height: int
    meta_line_height: int
    heading_height: int
    row_gap: int
    section_gap: int
    inline_gap: int
    time_column_width: int


class MetricsCalculator:
    def __init__(self, theme: CalendarTheme, fonts: FontProvider) -> None:
        self._theme = theme
        self._fonts = fonts

    def for_scale(self, scale: float) -> ScaledMetrics:
        theme, fonts = self._theme, self._fonts
        heading, time_size = round(theme.heading_size * scale), round(theme.time_size * scale)
        title, meta = round(theme.event_title_size * scale), round(theme.meta_size * scale)
        return ScaledMetrics(
            scale=scale,
            heading_size=heading,
            time_size=time_size,
            event_title_size=title,
            meta_size=meta,
            title_ascent=fonts.get(FontRole.BOLD, title).getmetrics()[0],
            title_line_height=fonts.line_height(FontRole.BOLD, title, leading=1.06),
            meta_line_height=fonts.line_height(FontRole.REGULAR, meta, leading=1.12),
            heading_height=round(fonts.line_height(FontRole.HEAVY, heading) * 1.45),
            row_gap=round(13 * scale),
            section_gap=round(16 * scale),
            inline_gap=round(18 * scale),
            time_column_width=round(fonts.get(FontRole.BOLD, time_size).getlength("00:00") + 22 * scale),
        )
