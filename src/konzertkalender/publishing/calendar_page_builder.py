"""The page the Kindle opens on wake-up: the calendar image itself, scaled to fit one screen, with every
event row tappable (it opens the event's page on the venue's website).

The tappable areas are transparent links laid over the image, positioned in percent of its height,
so they stay in place at any display size. A tiny script fits the image to the screen height for
browsers without "vh" support (the Kindle's browser bar takes some of the height).
"""

from __future__ import annotations

from html import escape

from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.german_labels import GermanCalendarLabels
from konzertkalender.rendering.rendered_calendar import LinkRegion, RegionKind, RenderedCalendar

REFRESH_SECONDS = 6 * 3600
STYLE = (
    "html,body{margin:0;padding:0;background:#fff}"
    "#kalender{position:relative;margin:0 auto;width:100%;max-width:ASPECTvh}"
    "#kalender img{display:block;width:100%;height:auto;border:0}"
    "#kalender a{position:absolute;left:0;right:0;display:block;background:rgba(255,255,255,0)}"
)
FIT_SCRIPT = (
    "(function(){var k=document.getElementById('kalender');"
    "function fit(){k.style.width=Math.min(window.innerWidth,Math.floor(window.innerHeight*RATIO))+'px';}"
    "fit();window.onresize=fit;})();"
)


class CalendarPageBuilder:
    def __init__(self, title: str, formatter: EventTextFormatter) -> None:
        self._title = title
        self._formatter = formatter

    def build(self, calendar: RenderedCalendar, program: WeekendProgram, image_src: str, list_href: str) -> str:
        width, height = calendar.image.size
        ratio = width / height
        window = program.window
        dates = GermanCalendarLabels.date_range(window.first_evening, window.last_evening)
        links = "\n".join(self._link(region, height, list_href) for region in calendar.regions)
        return (
            "<!DOCTYPE html>\n<html lang=\"de\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<meta http-equiv=\"refresh\" content=\"{REFRESH_SECONDS}\">"
            f"<title>{escape(self._title)} – {escape(dates)}</title>"
            f"<style>{STYLE.replace('ASPECT', f'{100 * ratio:.2f}')}</style></head><body>\n"
            f"<div id=\"kalender\"><img src=\"{escape(image_src, quote=True)}\" width=\"{width}\" "
            f"height=\"{height}\" alt=\"Konzertkalender {escape(dates, quote=True)}\">\n{links}\n</div>\n"
            f"<script>{FIT_SCRIPT.replace('RATIO', f'{ratio:.4f}')}</script>\n</body></html>\n"
        )

    def _link(self, region: LinkRegion, image_height: int, list_href: str) -> str:
        href, label = self._target(region, list_href)
        top = 100 * region.top / image_height
        size = 100 * (region.bottom - region.top) / image_height
        return (f'<a href="{escape(href, quote=True)}" title="{escape(label, quote=True)}" '
                f'style="top:{top:.2f}%;height:{size:.2f}%"></a>')

    def _target(self, region: LinkRegion, list_href: str) -> tuple[str, str]:
        event = region.event
        if region.kind is RegionKind.EVENT and event is not None:
            label = f"{self._formatter.time_label(event)} {event.title} – {self._formatter.venue_label(event)}"
            return event.url or list_href, label
        if region.kind is RegionKind.HIDDEN_EVENTS:
            return list_href, "Alle Events dieses Abends"
        return list_href, "Alle Events als Liste"
