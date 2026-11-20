"""Weekend window rules and the German/French date and time parsing."""

from __future__ import annotations

from datetime import date, datetime, time

import pytest
from conftest import TODAY, ZURICH

from konzertkalender.domain.weekend_window import WeekendWindow
from konzertkalender.parsing.date_parsing import VenueDateParser


@pytest.mark.parametrize("reference", [date(2026, 11, 23), date(2026, 11, 25), date(2026, 11, 28)])
def test_monday_to_saturday_map_to_the_same_weeks_thursday_to_saturday(reference):
    window = WeekendWindow.for_reference_date(reference)
    assert (window.first_evening, window.last_evening) == (date(2026, 11, 26), date(2026, 11, 28))


def test_sunday_maps_to_the_next_week():
    window = WeekendWindow.for_reference_date(date(2026, 11, 29))
    assert window.first_evening == date(2026, 12, 3)


def test_evening_rules_include_late_nights_and_exclude_afternoons():
    window = WeekendWindow.for_reference_date(date(2026, 11, 23))
    assert window.evening_of(datetime(2026, 11, 26, 20, 0, tzinfo=ZURICH)) == date(2026, 11, 26)
    assert window.evening_of(datetime(2026, 11, 29, 0, 30, tzinfo=ZURICH)) == date(2026, 11, 28)
    assert window.evening_of(datetime(2026, 11, 27, 14, 0, tzinfo=ZURICH)) is None
    assert window.evening_of(datetime(2026, 11, 25, 21, 0, tzinfo=ZURICH)) is None


@pytest.fixture
def parser() -> VenueDateParser:
    return VenueDateParser(TODAY)


@pytest.mark.parametrize(("text", "expected"), [
    ("Fr. 20.11.2026", date(2026, 11, 20)),
    ("Fr 20.11.26", date(2026, 11, 20)),
    ("27.11.", date(2026, 11, 27)),
    ("13.02.", date(2027, 2, 13)),  # past date far back -> next year
])
def test_numeric_dates(parser, text, expected):
    assert parser.numeric_date(text) == expected


@pytest.mark.parametrize(("text", "expected"), [
    ("So., 22. Nov. 2026 20:00 - 23:30", date(2026, 11, 22)),
    ("Fr. 20. November 2026 — 23:00", date(2026, 11, 20)),
    ("Freitag 20 November 2026", date(2026, 11, 20)),
    ("samedi 5 décembre", date(2026, 12, 5)),
])
def test_named_month_dates(parser, text, expected):
    assert parser.named_month_date(text) == expected


@pytest.mark.parametrize(("text", "expected"), [
    ("Doors 23:00", time(23, 0)),
    ("20h30", time(20, 30)),
    ("20.00 Uhr", time(20, 0)),
    ("22 Uhr", time(22, 0)),
    ("16–19 Uhr", time(16, 0)),
    ("Fr. 20.11.2026 | Tür 19:30", time(19, 30)),
    ("So., 22. Nov. 2026 20:00 - 23:30", time(20, 0)),
])
def test_times(parser, text, expected):
    assert parser.time_of_day(text) == expected


def test_labeled_time_prefers_start_over_doors(parser):
    assert parser.labeled_time("Tür 19:30, Start 20:00", ("start",)) == time(20, 0)


def test_relative_days_and_iso_without_trusting_offsets(parser):
    assert parser.relative_day("Morgen") == date(2026, 11, 21)
    assert parser.iso_date_and_time("2026-11-20T20:00:00-08:00") == (date(2026, 11, 20), time(20, 0))
