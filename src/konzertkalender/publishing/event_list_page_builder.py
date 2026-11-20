"""The complete list of the weekend's events as plain HTML, grouped like the image (evening, then
club), every event linking to its page on the
venue's website. Reached from the calendar page (footer, "+ N weitere"), so nothing is lost when the
image has to shorten titles or leave out events of a very full evening.

Kept deliberately simple (no JavaScript, no web fonts, basic CSS) so the Kindle's old
experimental browser renders it quickly.
"""

from __future__ import annotations

from html import escape

from konzertkalender.domain.event import Event
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.club_grouping import ClubGrouping
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.german_labels import GermanCalendarLabels

REFRESH_SECONDS = 6 * 3600
STYLE = """
body{font-family:sans-serif;margin:0 auto;max-width:46em;padding:.8em 1em 2em;color:#000;background:#fff}
h1{font-size:1.3em;margin:.2em 0 .4em}
.back{display:inline-block;color:#000;font-weight:bold;padding:.4em 0}
h2{background:#000;color:#fff;font-size:1.05em;letter-spacing:.05em;padding:.4em .6em;margin:1.1em 0 .2em}
table{width:100%;border-collapse:collapse}
td{vertical-align:top;padding:.55em .3em}
tr.club td{border-top:2px solid #999}
tr.first td{border-top:0}
td.club{font-weight:bold;width:7em}
td.time{font-weight:bold;text-align:right;white-space:nowrap;width:3.2em}
a{color:#000;text-decoration:none}
.title{font-weight:bold}
.meta{display:block;color:#222;font-weight:bold;font-size:.9em}
.empty{color:#333;padding:.6em .2em}
.footer{color:#333;font-size:.85em;margin-top:1.5em}
"""


class EventListPageBuilder:
    def __init__(self, title: str, formatter: EventTextFormatter, back_href: str = "./") -> None:
        self._title = title
        self._formatter = formatter
        self._club_grouping = ClubGrouping(formatter)
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
        heading = f"<h2>{escape(GermanCalendarLabels.evening_heading(evening).upper())}</h2>"
        if not events:
            return f'{heading}\n<div class="empty">Nichts gefunden</div>'
        starts = self._club_grouping.group_starts(events)
        rows = [self._event_row(event, start, index == 0) for index, (event, start) in enumerate(zip(events, starts))]
        return f"{heading}\n<table>\n" + "\n".join(rows) + "\n</table>"

    def _event_row(self, event: Event, starts_club: bool, is_first: bool) -> str:
        """Club (first event of a club only) | title and room/kind/genres, linked | start time."""
        row_class = " first" if is_first else ""
        club = escape(self._formatter.club_label(event)) if starts_club else ""
        href = escape(event.url or "#", quote=True)
        return (
            f'<tr class="{"club" if starts_club else "more"}{row_class}"><td class="club">{club}</td>'
            f'<td><a href="{href}"><span class="title">{escape(event.title)}</span>'
            f'<span class="meta">{escape(self._formatter.details_label(event))} ›</span></a></td>'
            f'<td class="time">{escape(self._formatter.time_label(event))}</td></tr>'
        )
