"""Fitting one event into a row.

Club name in the left column (only on the first row of each club), start time on the right, and in
between either two lines (title, then room/kind/genres) or one compact line (title · genres).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from konzertkalender.domain.event import Event
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_text_formatter import META_SEPARATOR, EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider, FontRole
from konzertkalender.rendering.layout_metrics import ScaledMetrics
from konzertkalender.rendering.meta_fonts import MetaFonts
from konzertkalender.rendering.text_fitter import ELLIPSIS, TextFitter

MIN_INLINE_TITLE_SHARE = 0.55


class RowStyle(Enum):
    STACKED = "stacked"
    INLINE = "inline"


@dataclass(frozen=True)
class EventRow:
    event: Event
    style: RowStyle
    club_label: str  # empty for further events of the same club on that evening
    time_label: str
    title_lines: tuple[str, ...]
    details_label: str
    details_x_offset: float  # one-line rows: where the details start, relative to the text column

    @property
    def starts_club_group(self) -> bool:
        return bool(self.club_label)

    def height(self, metrics: ScaledMetrics) -> int:
        if self.style is RowStyle.INLINE:
            return metrics.title_line_height + metrics.row_gap
        return len(self.title_lines) * metrics.title_line_height + metrics.meta_line_height + metrics.row_gap


class EventRowBuilder:
    def __init__(
        self, theme: CalendarTheme, fonts: FontProvider, fitter: TextFitter, formatter: EventTextFormatter
    ) -> None:
        self._theme = theme
        self._fonts = fonts
        self._meta_fonts = MetaFonts(fonts)
        self._fitter = fitter
        self._formatter = formatter

    def text_width(self, metrics: ScaledMetrics) -> float:
        """Width between the club column and the time column."""
        return self._theme.width - 2 * self._theme.margin - metrics.club_column_width - metrics.time_column_width

    def build(self, event: Event, metrics: ScaledMetrics, style: RowStyle, starts_club_group: bool) -> EventRow:
        club = self._club_label(event, metrics) if starts_club_group else ""
        if style is RowStyle.INLINE:
            return self._inline_row(event, metrics, club)
        return self._stacked_row(event, metrics, club)

    def _club_label(self, event: Event, metrics: ScaledMetrics) -> str:
        font = self._meta_fonts.club(metrics.meta_size)
        available = metrics.club_column_width - metrics.inline_gap
        return self._fitter.ellipsize(self._formatter.club_label(event), font, available)

    def _stacked_row(self, event: Event, metrics: ScaledMetrics, club: str) -> EventRow:
        width = self.text_width(metrics)
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        title_lines = self._fitter.wrap(event.title, title_font, width, self._theme.max_title_lines)
        details_font = self._meta_fonts.details(metrics.meta_size)
        details = self._fitter.ellipsize(self._formatter.details_label(event), details_font, width)
        return EventRow(event, RowStyle.STACKED, club, self._formatter.time_label(event), tuple(title_lines),
                        details, 0)

    def _inline_row(self, event: Event, metrics: ScaledMetrics, club: str) -> EventRow:
        width = self.text_width(metrics)
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        details_font = self._meta_fonts.details(metrics.meta_size)
        details = META_SEPARATOR + self._formatter.compact_details_label(event)
        title_budget = max(width * MIN_INLINE_TITLE_SHARE, width - self._fitter.width(details, details_font))
        title = self._fitter.ellipsize(event.title, title_font, title_budget)
        offset = self._fitter.width(title, title_font)
        details = self._fitter.ellipsize(details, details_font, width - offset)
        if not details.strip(" ·" + ELLIPSIS):
            details = ""  # no room left for anything readable
        return EventRow(event, RowStyle.INLINE, club, self._formatter.time_label(event), (title,), details, offset)
