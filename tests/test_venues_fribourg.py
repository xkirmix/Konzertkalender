"""Parsers of the Fribourg venues (incl. Bad Bonn) against small fixture pages."""

from __future__ import annotations

from datetime import date, datetime

from conftest import ZURICH, fixture_text

from konzertkalender.domain.event import EventKind
from konzertkalender.venues.fribourg.bad_bonn_source import BadBonnSource
from konzertkalender.venues.fribourg.fri_son_source import FriSonSource
from konzertkalender.venues.fribourg.nouveau_monde_source import NouveauMondeSource

SOYBOMB = "https://club.badbonn.ch/archive/2026/soybomb-cedric-blaser"
ELR = "https://club.badbonn.ch/archive/2026/e-l-r-abraham"


def test_bad_bonn_carries_month_reads_year_from_url_and_genres_from_details(make_toolkit, weekend):
    fetcher, toolkit = make_toolkit({
        BadBonnSource.program_url: fixture_text("bad_bonn.html"),
        SOYBOMB: fixture_text("bad_bonn_soybomb.html"),
        ELR: fixture_text("bad_bonn_elr.html"),
    })
    soybomb, elr, electrodudes, karaoke = BadBonnSource(toolkit).fetch_events(weekend)
    assert soybomb.starts_at == datetime(2026, 11, 27, 20, 30, tzinfo=ZURICH)
    assert soybomb.genres == ("Indie", "Prog", "Psych")
    assert elr.starts_at.date() == date(2026, 11, 28)  # month "Nov" carried over from the row above
    assert elr.genres == ("Doom", "Drone", "Metal")
    assert electrodudes.kind is EventKind.PARTY and electrodudes.starts_at.date() == date(2026, 12, 25)
    assert karaoke.starts_at.date() == date(2027, 1, 9)
    assert fetcher.requested == [BadBonnSource.program_url, SOYBOMB, ELR]  # no detail pages outside the weekend


def test_fri_son_reads_performers_doors_genres_and_status(make_toolkit, weekend):
    _, toolkit = make_toolkit({FriSonSource.program_url: fixture_text("fri_son.html")})
    wood_heart, cancelled = FriSonSource(toolkit).fetch_events(weekend)
    assert wood_heart.title == "WOOD'HEART (CH)"
    assert wood_heart.starts_at == datetime(2026, 11, 28, 22, 0, tzinfo=ZURICH)
    assert wood_heart.genres == ("Hip-Hop", "Rap")
    assert wood_heart.kind is EventKind.CONCERT
    assert wood_heart.url == "https://www.fri-son.ch/de/evenement/wood-heart"
    assert cancelled.is_cancelled


def test_nouveau_monde_maps_codes_relative_days_and_french_times(make_toolkit, weekend):
    _, toolkit = make_toolkit({NouveauMondeSource.program_url: fixture_text("nouveau_monde.html")})
    metal, before, brunch = NouveauMondeSource(toolkit).fetch_events(weekend)
    assert metal.kind is EventKind.CONCERT
    assert metal.starts_at == datetime(2026, 11, 27, 20, 30, tzinfo=ZURICH)
    assert metal.genres == ("Metal",)
    assert before.starts_at == datetime(2026, 11, 21, 16, 0, tzinfo=ZURICH)  # "Morgen" seen on 20 Nov
    assert before.kind is EventKind.PARTY
    assert brunch.kind is EventKind.OTHER
