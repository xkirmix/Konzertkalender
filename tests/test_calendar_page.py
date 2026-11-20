"""The tappable calendar page, the full list page and the edition written for GitHub Pages."""

from __future__ import annotations

import re
from datetime import datetime

from conftest import ZURICH

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.event import Event, EventKind
from konzertkalender.publishing.calendar_page_builder import CalendarPageBuilder
from konzertkalender.publishing.event_list_page_builder import EventListPageBuilder
from konzertkalender.publishing.program_serializer import ProgramSerializer
from konzertkalender.publishing.site_publisher import SitePublisher
from konzertkalender.rendering.calendar_layout import CalendarLayoutPlanner
from konzertkalender.rendering.calendar_renderer import KindleCalendarRenderer
from konzertkalender.rendering.calendar_theme import CalendarTheme
from konzertkalender.rendering.event_text_formatter import EventTextFormatter
from konzertkalender.rendering.font_provider import FontProvider
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.rendered_calendar import RegionKind, RenderedCalendar
from konzertkalender.rendering.text_fitter import TextFitter
from konzertkalender.selection.event_selection_manager import EventSelectionManager

FOOTER = FooterInfo(datetime(2026, 11, 23, 6, 0, tzinfo=ZURICH), ("ISC",), ())
LINK = re.compile(r'<a href="([^"]+)" title="[^"]*" style="top:([\d.]+)%;height:([\d.]+)%">')


def concert(title: str, day: int, **extra) -> Event:
    return Event(venue="ISC", title=title, starts_at=datetime(2026, 11, day, 20, 0, tzinfo=ZURICH),
                 kind=extra.pop("kind", EventKind.CONCERT), **extra)


def render(event_count: int, weekend):
    events = [concert(f"Band {index}", 26 + index % 3, url=f"https://isc-club.ch/programm/band-{index}/",
                      genres=("Rock",)) for index in range(event_count)]
    program = EventSelectionManager({EventKind.CONCERT}).select(events, weekend)
    theme = CalendarTheme()
    fonts, fitter, formatter = FontProvider(theme.fonts), TextFitter(), EventTextFormatter()
    renderer = KindleCalendarRenderer(theme, fonts, CalendarLayoutPlanner(theme, fonts, fitter, formatter), fitter)
    return renderer.render(program, FOOTER), program


def page_for(calendar: RenderedCalendar, program) -> str:
    return CalendarPageBuilder("Bern", EventTextFormatter()).build(calendar, program, "kalender.png?v=abc", "liste.html")


def test_every_shown_event_gets_a_tappable_band_from_top_to_bottom(weekend):
    calendar, _ = render(9, weekend)
    event_regions = [region for region in calendar.regions if region.kind is RegionKind.EVENT]
    assert len(event_regions) == 9
    assert [region.top for region in event_regions] == sorted(region.top for region in event_regions)
    assert all(0 <= region.top < region.bottom <= calendar.image.height for region in calendar.regions)


def test_calendar_page_links_events_and_sends_the_rest_to_the_list(weekend):
    calendar, program = render(80, weekend)  # overfull: evenings end with "+ N weitere Events"
    links = LINK.findall(page_for(calendar, program))
    hrefs = [href for href, _, _ in links]
    assert any(href.startswith("https://isc-club.ch/programm/band-") for href in hrefs)
    assert hrefs.count("liste.html") >= 2  # "+ N weitere" and the footer
    assert all(float(top) + float(height) <= 100.01 for _, top, height in links)


def test_calendar_page_shows_the_versioned_image(weekend):
    calendar, program = render(3, weekend)
    page = page_for(calendar, program)
    assert 'src="kalender.png?v=abc"' in page
    assert 'width="1072" height="1448"' in page


def test_publisher_writes_image_page_list_and_data(tmp_path, weekend):
    calendar, program = render(5, weekend)
    formatter = EventTextFormatter()
    publisher = SitePublisher(tmp_path, CalendarPageBuilder("Bern", formatter),
                              EventListPageBuilder("Bern", formatter), ProgramSerializer())
    written = publisher.publish(calendar, program, FOOTER, [SourceStatus("ISC", event_count=5)])
    assert sorted(path.name for path in written) == ["index.html", "kalender.json", "kalender.png", "liste.html"]
    assert re.search(r'src="kalender\.png\?v=[0-9a-f]{10}"', (tmp_path / "index.html").read_text())
    assert 'href="./"' in (tmp_path / "liste.html").read_text()


def test_one_line_rows_name_the_kind_only_when_genres_are_missing():
    formatter = EventTextFormatter()
    assert formatter.compact_details_label(concert("A", 27, genres=("Punk", "Garage"))) == " · Punk, Garage"
    assert formatter.compact_details_label(concert("B", 27, kind=EventKind.PARTY)) == " · Party"
