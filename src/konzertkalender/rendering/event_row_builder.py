"""Fitting one event into a row: two lines (title, then venue/genres) or one compact line."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from konzertkalender.domain.event import Event
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider, FontRole
from konzertkalender.rendering.layout_metrics import ScaledMetrics
from konzertkalender.rendering.text_fitter import TextFitter

VENUE_SHARE_OF_META = 0.6
MIN_INLINE_TITLE_SHARE = 0.5


class RowStyle(Enum):
    STACKED = "stacked"
    INLINE = "inline"


@dataclass(frozen=True)
class EventRow:
    event: Event
    style: RowStyle
    time_label: str
    title_lines: tuple[str, ...]
    venue_label: str
    details_label: str
    meta_x_offset: float  # where venue/genres start, relative to the title column

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
        self._fitter = fitter
        self._formatter = formatter

    def build(self, event: Event, metrics: ScaledMetrics, style: RowStyle) -> EventRow:
        text_width = self._theme.width - 2 * self._theme.margin - metrics.time_column_width
        if style is RowStyle.INLINE:
            return self._inline_row(event, metrics, text_width)
        return self._stacked_row(event, metrics, text_width)

    def _stacked_row(self, event: Event, metrics: ScaledMetrics, text_width: float) -> EventRow:
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        title_lines = self._fitter.wrap(event.title, title_font, text_width, self._theme.max_title_lines)
        venue, details = self._meta(event, metrics, text_width)
        return EventRow(event, RowStyle.STACKED, self._formatter.time_label(event), tuple(title_lines), venue, details, 0)

    def _inline_row(self, event: Event, metrics: ScaledMetrics, text_width: float) -> EventRow:
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        meta_width = self._meta_width(event, metrics)
        title_budget = max(text_width * MIN_INLINE_TITLE_SHARE, text_width - meta_width - metrics.inline_gap)
        title = self._fitter.ellipsize(event.title, title_font, title_budget)
        meta_x_offset = self._fitter.width(title, title_font) + metrics.inline_gap
        venue, details = self._meta(event, metrics, text_width - meta_x_offset)
        return EventRow(event, RowStyle.INLINE, self._formatter.time_label(event), (title,), venue, details, meta_x_offset)

    def _meta(self, event: Event, metrics: ScaledMetrics, available: float) -> tuple[str, str]:
        venue_font = self._fonts.get(FontRole.SEMIBOLD, metrics.meta_size)
        details_font = self._fonts.get(FontRole.REGULAR, metrics.meta_size)
        venue = self._fitter.ellipsize(self._formatter.venue_label(event), venue_font, available * VENUE_SHARE_OF_META)
        details_width = available - self._fitter.width(venue, venue_font)
        return venue, self._fitter.ellipsize(self._formatter.details_label(event), details_font, details_width)

    def _meta_width(self, event: Event, metrics: ScaledMetrics) -> float:
        venue_font = self._fonts.get(FontRole.SEMIBOLD, metrics.meta_size)
        details_font = self._fonts.get(FontRole.REGULAR, metrics.meta_size)
        return (self._fitter.width(self._formatter.venue_label(event), venue_font)
                + self._fitter.width(self._formatter.details_label(event), details_font))
