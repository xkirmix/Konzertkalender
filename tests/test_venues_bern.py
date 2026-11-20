"""Parsers of the Bern venues against small fixture pages that mirror the real HTML structure."""

from __future__ import annotations

from datetime import datetime

from conftest import ZURICH, fixture_text

from konzertkalender.domain.event import EventKind
from konzertkalender.venues.bern.cafe_kairo_source import CafeKairoSource
from konzertkalender.venues.bern.cafete_source import CafeteSource
from konzertkalender.venues.bern.dachstock_source import DachstockSource
from konzertkalender.venues.bern.gaskessel_source import GaskesselSource
from konzertkalender.venues.bern.isc_source import IscSource
from konzertkalender.venues.bern.progr_source import ProgrSource
from konzertkalender.venues.bern.roessli_source import RoessliSource


def by_title(events):
    return {event.title: event for event in events}


def test_dachstock_reads_json_ld_kind_and_genres(make_toolkit, weekend):
    _, toolkit = make_toolkit({DachstockSource.program_url: fixture_text("dachstock.html")})
    events = by_title(DachstockSource(toolkit).fetch_events(weekend))
    assert events["Pixel Grip"].kind is EventKind.CONCERT
    assert events["Pixel Grip"].genres == ("Industrial", "EBM", "Synthpop")
    assert events["Pixel Grip"].starts_at == datetime(2026, 11, 27, 21, 0, tzinfo=ZURICH)
    assert events["Darkside"].kind is EventKind.PARTY
    assert events["Darkside"].genres == ("Drum and Bass",)
    assert events["Schachturnier im Souli"].kind is EventKind.OTHER


def test_gaskessel_reads_doors_time_country_and_kind(make_toolkit, weekend):
    _, toolkit = make_toolkit({GaskesselSource.program_url: fixture_text("gaskessel.html")})
    events = by_title(GaskesselSource(toolkit).fetch_events(weekend))
    party = events["ULTRA DANCE w/ Lolalita (BEL)"]
    assert party.starts_at == datetime(2026, 11, 27, 23, 0, tzinfo=ZURICH)
    assert party.kind is EventKind.PARTY
    assert party.genres == ("Jumpstyle", "Hard Dance", "Hardcore")
    assert party.url == "https://gaskessel.ch/programm/ultra-dance/"
    assert events["Club Quiz"].kind is EventKind.OTHER


def test_isc_fetches_start_times_only_for_the_weekend(make_toolkit, weekend):
    detail_url = "https://isc-club.ch/programm/the-monsters/"
    fetcher, toolkit = make_toolkit({IscSource.program_url: fixture_text("isc.html"), detail_url: fixture_text("isc_detail.html")})
    events = by_title(IscSource(toolkit).fetch_events(weekend))
    monsters = events["The Monsters – Bern-In-Hell Tour"]
    assert monsters.starts_at.hour == 20 and monsters.has_start_time
    assert monsters.genres == ("Garage Rock", "Trash Punk", "Rockabilly")
    assert events["Yndling"].is_cancelled and not events["Yndling"].has_start_time
    assert events["Later Party"].kind is EventKind.PARTY
    assert "https://isc-club.ch/programm/later/" not in fetcher.requested


def test_roessli_keeps_only_real_genres_from_mixed_tags(make_toolkit, weekend):
    _, toolkit = make_toolkit({RoessliSource.program_url: fixture_text("roessli.html")})
    events = RoessliSource(toolkit).fetch_events(weekend)
    assert len(events) == 2
    tight_finks, gvllow = events
    assert tight_finks.kind is EventKind.CONCERT  # "Support" in the title beats "DJ"
    assert tight_finks.genres == ("Powerpop", "Punk")
    assert gvllow.genres == ("Post Punk",)
    assert gvllow.starts_at == datetime(2026, 11, 22, 20, 0, tzinfo=ZURICH)


def test_cafete_reads_style_line(make_toolkit, weekend):
    _, toolkit = make_toolkit({CafeteSource.program_url: fixture_text("cafete.html")})
    (event,) = CafeteSource(toolkit).fetch_events(weekend)
    assert event.starts_at == datetime(2026, 11, 27, 22, 0, tzinfo=ZURICH)
    assert event.genres == ("Minimal Wave", "Acid", "Cold House")
    assert event.kind is EventKind.PARTY


def test_cafe_kairo_prefers_start_over_doors_and_finds_genres_in_text(make_toolkit, weekend):
    _, toolkit = make_toolkit({CafeKairoSource.program_url: fixture_text("cafe_kairo.html")})
    events = by_title(CafeKairoSource(toolkit).fetch_events(weekend))
    concert = events["The Monsters Plattentaufe"]
    assert concert.starts_at == datetime(2026, 11, 26, 21, 0, tzinfo=ZURICH)
    assert concert.kind is EventKind.CONCERT
    assert concert.genres == ("Rock", "Punk")
    assert events["Literatur aus dem Café Kairo"].kind is EventKind.OTHER


def test_progr_builds_title_venue_and_detail_link(make_toolkit, weekend):
    _, toolkit = make_toolkit({ProgrSource.program_url: fixture_text("progr.html")})
    jazz, exhibition = ProgrSource(toolkit).fetch_events(weekend)
    assert jazz.title == "Jazzwerkstatt presents: Keenan Ahrends 4tet"
    assert jazz.venue == "Sonarraum U64 (PROGR)"
    assert jazz.genres == ("Jazz", "Improvisation")
    assert jazz.url == "https://www.progr.ch/de/agenda/jazzwerkstatt-keenan-ahrends-4tet-8800/"
    assert exhibition.kind is EventKind.OTHER
    assert exhibition.starts_at.hour == 18  # "18–21 Uhr" starts at 18
