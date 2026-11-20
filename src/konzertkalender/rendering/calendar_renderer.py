"""Draws the planned calendar layout into a grayscale image for the Kindle.

It also records where every event (and the "+ N weitere" note and the footer) sits, so the web page
can make the very same image tappable.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.calendar_layout import CalendarLayoutPlanner, EveningBlock
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_row_builder import EventRow, RowStyle
from konzertkalender.rendering.font_provider import FontProvider, FontRole
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.frame_geometry import GAP_ABOVE_FOOTER_TEXT, FrameGeometry
from konzertkalender.rendering.german_labels import GermanCalendarLabels
from konzertkalender.rendering.layout_metrics import ScaledMetrics
from konzertkalender.rendering.rendered_calendar import LinkRegion, RegionKind, RenderedCalendar
from konzertkalender.rendering.text_fitter import TextFitter

HEADING_PADDING = 18
HEADING_RADIUS = 10
EMPTY_EVENING_NOTE = "Nichts gefunden"
FOOTER_HINT_GAP = 24


class KindleCalendarRenderer:
    def __init__(
        self,
        theme: CalendarTheme,
        fonts: FontProvider,
        planner: CalendarLayoutPlanner,
        fitter: TextFitter,
        footer_hint: str = "",
    ) -> None:
        self._theme = theme
        self._fonts = fonts
        self._planner = planner
        self._fitter = fitter
        self._geometry = FrameGeometry(theme, fonts)
        self._footer_hint = footer_hint

    def render(self, program: WeekendProgram, footer: FooterInfo) -> RenderedCalendar:
        layout = self._planner.plan(program)
        image = Image.new("L", (self._theme.width, self._theme.height), self._theme.paper)
        draw = ImageDraw.Draw(image)
        regions: list[LinkRegion] = []
        y = self._geometry.content_top()
        for block in layout.blocks:
            y = self._draw_block(draw, block, layout.metrics, y, regions)
        self._draw_footer(draw, footer)
        regions.append(LinkRegion(RegionKind.FOOTER, self._geometry.footer_top(), self._theme.height))
        return RenderedCalendar(image, tuple(regions))

    def _draw_block(self, draw: ImageDraw.ImageDraw, block: EveningBlock, metrics: ScaledMetrics, top: int,
                    regions: list[LinkRegion]) -> int:
        y = self._draw_heading(draw, block, metrics, top)
        for row in block.rows:
            row_top = y
            y = self._draw_row(draw, row, metrics, y)
            regions.append(LinkRegion(RegionKind.EVENT, row_top, y, row.event))
        note = GermanCalendarLabels.hidden_events(block.hidden_count) if block.hidden_count else (
            EMPTY_EVENING_NOTE if not block.rows else "")
        if note:
            note_top = y
            note_font = self._fonts.get(FontRole.SEMIBOLD, metrics.meta_size)
            draw.text((self._theme.margin + metrics.time_column_width, y), note, font=note_font,
                      fill=self._theme.details_ink, anchor="la")
            y += metrics.meta_line_height + metrics.row_gap
            if block.hidden_count:
                regions.append(LinkRegion(RegionKind.HIDDEN_EVENTS, note_top, y))
        return y + metrics.section_gap

    def _draw_heading(self, draw: ImageDraw.ImageDraw, block: EveningBlock, metrics: ScaledMetrics, top: int) -> int:
        """The black bar with the evening's date and how many events it has."""
        theme = self._theme
        left, right, bottom = theme.margin, theme.width - theme.margin, top + metrics.heading_height
        draw.rounded_rectangle((left, top, right, bottom), radius=HEADING_RADIUS, fill=theme.ink)
        middle = (top + bottom) / 2
        heading = GermanCalendarLabels.evening_heading(block.evening).upper()
        draw.text((left + HEADING_PADDING, middle), heading, font=self._fonts.get(FontRole.HEAVY, metrics.heading_size),
                  fill=theme.paper, anchor="lm")
        count = GermanCalendarLabels.event_count(len(block.rows) + block.hidden_count)
        count_font = self._fonts.get(FontRole.SEMIBOLD, round(metrics.heading_size * 0.85))
        draw.text((right - HEADING_PADDING, middle), count, font=count_font, fill=theme.paper, anchor="rm")
        return bottom + metrics.row_gap

    def _draw_row(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics, top: int) -> int:
        if row.style is RowStyle.INLINE:
            return self._draw_inline_row(draw, row, metrics, top)
        return self._draw_stacked_row(draw, row, metrics, top)

    def _draw_stacked_row(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics, top: int) -> int:
        """Time and title on the first line(s), venue · kind · genres below."""
        theme = self._theme
        text_x = theme.margin + metrics.time_column_width
        time_font = self._fonts.get(FontRole.BOLD, metrics.time_size)
        draw.text((theme.margin, top), row.time_label, font=time_font, fill=theme.ink, anchor="la")
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        y = top
        for line in row.title_lines:
            draw.text((text_x, y), line, font=title_font, fill=theme.ink, anchor="la")
            y += metrics.title_line_height
        self._draw_meta(draw, row, metrics, text_x, y, anchor="la")
        return y + metrics.meta_line_height + metrics.row_gap

    def _draw_inline_row(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics, top: int) -> int:
        """Everything on one baseline: time, title, then venue · kind · genres."""
        theme = self._theme
        text_x = theme.margin + metrics.time_column_width
        baseline = top + metrics.title_ascent
        time_font = self._fonts.get(FontRole.BOLD, metrics.time_size)
        draw.text((theme.margin, baseline), row.time_label, font=time_font, fill=theme.ink, anchor="ls")
        title_font = self._fonts.get(FontRole.BOLD, metrics.event_title_size)
        draw.text((text_x, baseline), row.title_lines[0], font=title_font, fill=theme.ink, anchor="ls")
        self._draw_meta(draw, row, metrics, text_x + row.meta_x_offset, baseline, anchor="ls")
        return top + metrics.title_line_height + metrics.row_gap

    def _draw_meta(self, draw: ImageDraw.ImageDraw, row: EventRow, metrics: ScaledMetrics,
                   x: float, y: float, anchor: str) -> None:
        venue_font = self._fonts.get(FontRole.SEMIBOLD, metrics.meta_size)
        draw.text((x, y), row.venue_label, font=venue_font, fill=self._theme.venue_ink, anchor=anchor)
        details_font = self._fonts.get(FontRole.REGULAR, metrics.meta_size)
        details_x = x + venue_font.getlength(row.venue_label)
        draw.text((details_x, y), row.details_label, font=details_font, fill=self._theme.details_ink, anchor=anchor)

    def _draw_footer(self, draw: ImageDraw.ImageDraw, footer: FooterInfo) -> None:
        theme = self._theme
        left, right, top = theme.margin, theme.width - theme.margin, self._geometry.footer_top()
        draw.line((left, top, right, top), fill=theme.muted_ink, width=2)
        font = self._fonts.get(FontRole.REGULAR, theme.footer_size)
        hint_font = self._fonts.get(FontRole.SEMIBOLD, theme.footer_size)
        hint_width = hint_font.getlength(self._footer_hint) if self._footer_hint else 0
        status = f"Stand {GermanCalendarLabels.timestamp(footer.generated_at)} · {footer.summary}"
        text_y = top + GAP_ABOVE_FOOTER_TEXT
        status_width = right - left - (hint_width + FOOTER_HINT_GAP if hint_width else 0)
        draw.text((left, text_y), self._fitter.ellipsize(status, font, status_width), font=font,
                  fill=theme.secondary_ink, anchor="la")
        if self._footer_hint:
            draw.text((right, text_y), self._footer_hint, font=hint_font, fill=theme.ink, anchor="ra")
