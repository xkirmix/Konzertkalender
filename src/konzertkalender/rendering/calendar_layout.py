"""Planning the layout so the whole weekend fits on one screen.

Order of attempts: two-line rows from the largest text scale down to `min_stacked_scale`, then
compact one-line rows down to `min_scale`. If that is still too tall, the fullest evenings are
trimmed and show "+ N weitere Events" instead.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, replace
from datetime import date

from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_row_builder import EventRow, EventRowBuilder, RowStyle
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider
from konzertkalender.rendering.frame_geometry import FrameGeometry
from konzertkalender.rendering.layout_metrics import MetricsCalculator, ScaledMetrics
from konzertkalender.rendering.text_fitter import TextFitter


@dataclass(frozen=True)
class EveningBlock:
    evening: date
    rows: tuple[EventRow, ...]
    hidden_count: int = 0


@dataclass(frozen=True)
class CalendarLayout:
    metrics: ScaledMetrics
    blocks: tuple[EveningBlock, ...]


class CalendarLayoutPlanner:
    def __init__(
        self, theme: CalendarTheme, fonts: FontProvider, fitter: TextFitter, formatter: EventTextFormatter
    ) -> None:
        self._theme = theme
        self._metrics = MetricsCalculator(theme, fonts)
        self._rows = EventRowBuilder(theme, fonts, fitter, formatter)
        self._available_height = FrameGeometry(theme, fonts).content_height()

    def plan(self, program: WeekendProgram) -> CalendarLayout:
        layout: CalendarLayout | None = None
        for style, scale in self._attempts():
            layout = self._layout(program, self._metrics.for_scale(scale), style)
            if self.content_height(layout) <= self._available_height:
                return layout
        return self._trim(layout)

    def content_height(self, layout: CalendarLayout) -> int:
        return sum(self._block_height(block, layout.metrics) for block in layout.blocks)

    def _block_height(self, block: EveningBlock, metrics: ScaledMetrics) -> int:
        rows = sum(row.height(metrics) for row in block.rows)
        note = metrics.meta_line_height + metrics.row_gap if block.hidden_count or not block.rows else 0
        return metrics.heading_height + metrics.row_gap + rows + note + metrics.section_gap

    def _trim(self, layout: CalendarLayout) -> CalendarLayout:
        blocks = list(layout.blocks)
        while self.content_height(replace(layout, blocks=tuple(blocks))) > self._available_height:
            fullest = max(range(len(blocks)), key=lambda index: len(blocks[index].rows))
            block = blocks[fullest]
            if len(block.rows) <= 1:
                break
            blocks[fullest] = EveningBlock(block.evening, block.rows[:-1], block.hidden_count + 1)
        return replace(layout, blocks=tuple(blocks))

    def _layout(self, program: WeekendProgram, metrics: ScaledMetrics, style: RowStyle) -> CalendarLayout:
        blocks = tuple(
            EveningBlock(evening, tuple(self._rows.build(event, metrics, style) for event in program.events_on(evening)))
            for evening in program.window.evenings
        )
        return CalendarLayout(metrics=metrics, blocks=blocks)

    def _attempts(self) -> Iterator[tuple[RowStyle, float]]:
        for scale in self._scales(self._theme.min_stacked_scale):
            yield RowStyle.STACKED, scale
        for scale in self._scales(self._theme.min_scale):
            yield RowStyle.INLINE, scale

    def _scales(self, smallest: float) -> Iterator[float]:
        scale = self._theme.max_scale
        while scale >= smallest - 1e-9:
            yield round(scale, 3)
            scale -= self._theme.scale_step
