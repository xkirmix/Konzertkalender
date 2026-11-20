"""Plain-text overview of an update run, printed to the terminal and the GitHub Actions log."""

from __future__ import annotations

from collections.abc import Sequence

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.german_labels import GermanCalendarLabels


class TextSummaryWriter:
    def __init__(self, formatter: EventTextFormatter) -> None:
        self._formatter = formatter

    def render(self, program: WeekendProgram, statuses: Sequence[SourceStatus]) -> str:
        lines = ["Quellen:"]
        for status in statuses:
            state = "ok" if status.is_healthy else f"PROBLEM ({status.error or 'keine Events gefunden'})"
            lines.append(f"  {status.venue_name:<15} {status.event_count:>3} Events  {state}")
        for evening in program.window.evenings:
            lines.append(f"\n{GermanCalendarLabels.evening_heading(evening)}:")
            for event in program.events_on(evening) or ():
                genres = ", ".join(event.genres)
                lines.append(f"  {self._formatter.time_label(event):>5}  {event.title}  [{event.venue} · {event.kind.label}"
                             f"{' · ' + genres if genres else ''}]")
            if not program.events_on(evening):
                lines.append("  (nichts gefunden)")
        return "\n".join(lines)
