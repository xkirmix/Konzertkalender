"""Selection of the weekend program, the rendered image and the clickable page."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from conftest import ZURICH

from konzertkalender.domain.event import Event, EventKind
from konzertkalender.publishing.event_list_page_builder import EventListPageBuilder
from konzertkalender.rendering.calendar_layout import CalendarLayoutPlanner
from konzertkalender.rendering.calendar_renderer import KindleCalendarRenderer
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.text_fitter import TextFitter
from konzertkalender.selection.event_selection_manager import EventSelectionManager

FOOTER = FooterInfo(datetime(2026, 11, 23, 6, 0, tzinfo=ZURICH), ("ISC",), ("PROGR",))


def make_event(title: str, day: int, hour: int, kind: EventKind = EventKind.CONCERT, venue: str = "ISC", **extra) -> Event:
    return Event(venue=venue, title=title, starts_at=datetime(2026, 11, day, hour, 0, tzinfo=ZURICH), kind=kind, **extra)


def test_selection_filters_kinds_cancellations_and_duplicates(weekend):
    events = [
        make_event("Late Night", 29, 1, EventKind.PARTY),  # Saturday night after midnight
        make_event("Band", 27, 20),
        make_event("band", 27, 20),  # duplicate (case-insensitive)
        make_event("Lesung", 27, 19, EventKind.OTHER),
        make_event("Abgesagt", 26, 21, is_cancelled=True),
        make_event("Wednesday", 25, 21),
    ]
    program = EventSelectionManager({EventKind.CONCERT, EventKind.PARTY}).select(events, weekend)
    assert [event.title for event in program.events_on(date(2026, 11, 27))] == ["Band"]
    assert [event.title for event in program.events_on(date(2026, 11, 28))] == ["Late Night"]
    assert program.event_count == 2


def build_renderer() -> tuple[KindleCalendarRenderer, CalendarLayoutPlanner]:
    theme = CalendarTheme()
    fonts, fitter, formatter = FontProvider(theme.fonts), TextFitter(), EventTextFormatter()
    planner = CalendarLayoutPlanner(theme, fonts, fitter, formatter)
    return KindleCalendarRenderer(theme, fonts, planner, fitter, "Details"), planner


def program_with(event_count: int, weekend):
    events = [make_event(f"Event {index} mit einem recht langen Titel", 26 + index % 3, 19 + index % 4)
              for index in range(event_count)]
    return EventSelectionManager({EventKind.CONCERT}).select(events, weekend)


def test_image_has_kindle_size_and_grayscale(weekend):
    renderer, _ = build_renderer()
    image = renderer.render(program_with(6, weekend), FOOTER).image
    assert image.size == (1072, 1448) and image.mode == "L"


def test_many_events_switch_to_compact_rows_and_finally_trim(weekend):
    _, planner = build_renderer()
    roomy = planner.plan(program_with(6, weekend))
    crowded = planner.plan(program_with(24, weekend))  # a busy real weekend has 20-25 events
    overfull = planner.plan(program_with(80, weekend))
    assert roomy.blocks[0].rows[0].style.value == "stacked"
    assert crowded.blocks[0].rows[0].style.value == "inline"
    assert sum(block.hidden_count for block in crowded.blocks) == 0
    assert sum(block.hidden_count for block in overfull.blocks) > 0


def test_event_list_page_links_every_event(weekend):
    events = [make_event("The Monsters", 27, 20, url="https://isc-club.ch/programm/the-monsters/", genres=("Rock",))]
    program = EventSelectionManager({EventKind.CONCERT}).select(events, weekend)
    page = EventListPageBuilder("Bern", EventTextFormatter()).build(program, FOOTER)
    assert 'href="https://isc-club.ch/programm/the-monsters/"' in page
    assert "FREITAG 27. NOVEMBER" in page and "1/2 Clubs gelesen · keine Daten: PROGR" in page
    assert page.count('class="empty"') == 2  # Thursday and Saturday without events


def test_date_range_label_handles_month_change():
    from konzertkalender.rendering.german_labels import GermanCalendarLabels

    label = GermanCalendarLabels.date_range(date(2026, 12, 31), date(2026, 12, 31) + timedelta(days=2))
    assert label == "Do 31. Dezember – Sa 2. Januar 2027"
