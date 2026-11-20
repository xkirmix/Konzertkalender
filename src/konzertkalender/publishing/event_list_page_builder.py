"""The complete list of the weekend's events as plain HTML, every event linking to its page on the
venue's website. Reached from the calendar page (footer, "+ N weitere"), so nothing is lost when the
image has to shorten titles or leave out events of a very full evening.

Kept deliberately simple (no JavaScript, no web fonts, basic CSS) so the Kindle's old
experimental browser renders it quickly.
"""

from __future__ import annotations

from html import escape

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.german_labels import GermanCalendarLabels

REFRESH_SECONDS = 6 * 3600
STYLE = """
body{font-family:sans-serif;margin:0 auto;max-width:46em;padding:.8em 1em 2em;color:#000;background:#fff}
h1{font-size:1.3em;margin:.2em 0 .4em}
.back{display:inline-block;color:#000;font-weight:bold;padding:.4em 0}
h2{background:#000;color:#fff;font-size:1.05em;letter-spacing:.05em;padding:.4em .6em;margin:1.1em 0 .2em}
a.event{display:block;color:#000;text-decoration:none;border-bottom:1px solid #aaa;padding:.65em .2em}
.time{display:inline-block;width:3.6em;font-weight:bold}
.title{font-weight:bold}
.meta{display:block;margin-left:3.6em;color:#444;font-size:.92em}
.venue{font-weight:bold;color:#222}
.empty{color:#666;padding:.6em .2em}
.footer{color:#555;font-size:.85em;margin-top:1.5em}
"""


class EventListPageBuilder:
    def __init__(self, title: str, formatter: EventTextFormatter, back_href: str = "./") -> None:
        self._title = title
        self._formatter = formatter
        self._back_href = back_href

    def build(self, program: WeekendProgram, footer: FooterInfo) -> str:
        window = program.window
        dates = GermanCalendarLabels.date_range(window.first_evening, window.last_evening)
        sections = "\n".join(self._evening_section(program, evening) for evening in window.evenings)
        return (
            "<!DOCTYPE html>\n<html lang=\"de\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<meta http-equiv=\"refresh\" content=\"{REFRESH_SECONDS}\">"
            f"<title>{escape(self._title)} – Alle Events</title><style>{STYLE}</style></head><body>\n"
            f"<a class=\"back\" href=\"{escape(self._back_href, quote=True)}\">‹ Kalender</a>\n"
            f"<h1>Alle Events · {escape(dates)}</h1>\n{sections}\n"
            f"<div class=\"footer\">Stand {escape(GermanCalendarLabels.timestamp(footer.generated_at))} · "
            f"{escape(footer.summary)} · Eintrag antippen für Details</div>\n</body></html>\n"
        )

    def _evening_section(self, program: WeekendProgram, evening) -> str:
        events = program.events_on(evening)
        heading = escape(GermanCalendarLabels.evening_heading(evening).upper())
        body = "\n".join(self._event_link(event) for event in events) or '<div class="empty">Nichts gefunden</div>'
        return f"<h2>{heading}</h2>\n{body}"

    def _event_link(self, event: Event) -> str:
        href = escape(event.url or "#", quote=True)
        return (
            f'<a class="event" href="{href}"><span class="time">{escape(self._formatter.time_label(event))}</span>'
            f'<span class="title">{escape(event.title)}</span>'
            f'<span class="meta"><span class="venue">{escape(self._formatter.venue_label(event))}</span>'
            f"{escape(self._formatter.details_label(event))} ›</span></a>"
        )
