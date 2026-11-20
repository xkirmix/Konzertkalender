"""An e-ink friendly HTML page where every event links to its page on the venue's website.

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
h1{font-size:1.9em;margin:0}
.subtitle{font-weight:bold;color:#333;margin:.2em 0 .6em;border-bottom:.25em solid #000;padding-bottom:.5em}
h2{background:#000;color:#fff;font-size:1.05em;letter-spacing:.05em;padding:.4em .6em;margin:1.1em 0 .2em}
a.event{display:block;color:#000;text-decoration:none;border-bottom:1px solid #aaa;padding:.65em .2em}
.time{display:inline-block;width:3.6em;font-weight:bold}
.title{font-weight:bold}
.meta{display:block;margin-left:3.6em;color:#444;font-size:.92em}
.venue{font-weight:bold;color:#222}
.empty{color:#666;padding:.6em .2em}
.footer{color:#555;font-size:.85em;margin-top:1.5em}
"""


class ClickablePageBuilder:
    def __init__(self, title: str, subtitle_prefix: str, formatter: EventTextFormatter) -> None:
        self._title = title
        self._subtitle_prefix = subtitle_prefix
        self._formatter = formatter

    def build(self, program: WeekendProgram, footer: FooterInfo) -> str:
        window = program.window
        subtitle = f"{self._subtitle_prefix} · {GermanCalendarLabels.date_range(window.first_evening, window.last_evening)}"
        sections = "\n".join(self._evening_section(program, evening) for evening in window.evenings)
        return (
            "<!DOCTYPE html>\n<html lang=\"de\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
            f"<meta http-equiv=\"refresh\" content=\"{REFRESH_SECONDS}\">"
            f"<title>{escape(self._title)} – {escape(subtitle)}</title><style>{STYLE}</style></head><body>\n"
            f"<h1>{escape(self._title)}</h1><div class=\"subtitle\">{escape(subtitle)}</div>\n{sections}\n"
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
