"""All pixel sizes of the event list at one text scale."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.font_provider import FontProvider, FontRole
from konzertkalender.rendering.meta_fonts import MetaFonts

TIME_PATTERN = "00:00"


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
    club_column_width: int  # left column with the club name, including the gap after it
    time_column_width: int  # right column with the start time, including the gap before it


class MetricsCalculator:
    def __init__(self, theme: CalendarTheme, fonts: FontProvider) -> None:
        self._theme = theme
        self._fonts = fonts
        self._meta_fonts = MetaFonts(fonts)

    def for_scale(self, scale: float, club_labels: Iterable[str] = ()) -> ScaledMetrics:
        theme, fonts = self._theme, self._fonts
        heading, time_size = round(theme.heading_size * scale), round(theme.time_size * scale)
        title, meta = round(theme.event_title_size * scale), round(theme.meta_size * scale)
        gap = round(theme.inline_gap * scale)
        return ScaledMetrics(
            scale=scale,
            heading_size=heading,
            time_size=time_size,
            event_title_size=title,
            meta_size=meta,
            title_ascent=fonts.get(FontRole.BOLD, title).getmetrics()[0],
            title_line_height=fonts.line_height(FontRole.BOLD, title, leading=1.06),
            meta_line_height=self._meta_fonts.details_line_height(meta),
            heading_height=round(fonts.line_height(FontRole.HEAVY, heading) * theme.heading_height_factor),
            row_gap=round(theme.row_gap * scale),
            section_gap=round(theme.section_gap * scale),
            inline_gap=gap,
            club_column_width=self._club_column_width(club_labels, meta, gap),
            time_column_width=round(self._meta_fonts.time(time_size).getlength(TIME_PATTERN)) + gap,
        )

    def _club_column_width(self, club_labels: Iterable[str], size: int, gap: int) -> int:
        """As wide as the longest club name, but never more than `club_column_max_share`."""
        font = self._meta_fonts.club(size)
        widest = max((font.getlength(label) for label in club_labels), default=0.0)
        limit = (self._theme.width - 2 * self._theme.margin) * self._theme.club_column_max_share
        return math.ceil(min(widest, limit)) + gap  # rounding down would shorten the widest name
