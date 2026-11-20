"""Genre recognition in tags and prose, and the concert/party/other classification."""

from __future__ import annotations

from datetime import datetime

import pytest
from conftest import ZURICH

from konzertkalender.domain.event import EventKind
from konzertkalender.parsing.event_kind_classifier import EventKindClassifier

EVENING = datetime(2026, 11, 27, 20, 0, tzinfo=ZURICH)
LATE = datetime(2026, 11, 27, 23, 0, tzinfo=ZURICH)


@pytest.mark.parametrize("tag", ["Post Punk", "Vintage Indo-Pop", "Drum and Bass", "HARDTECHNO", "Psychedelic Folk", "80s"])
def test_recognized_genre_tags(genre_normalizer, tag):
    assert genre_normalizer.is_known_genre(tag)


@pytest.mark.parametrize("tag", ["House of the Dead", "Sumerian Rec", "BANGERSONLY", "Hits aus allen Jahrzehnten"])
def test_rejected_tags(genre_normalizer, tag):
    assert not genre_normalizer.is_known_genre(tag)


def test_tag_lists_drop_kind_words_format_caps_and_limit(genre_normalizer):
    tags = ["Konzert", "Industrial", "EBM", "SYNTHPOP", "Darkwave"]
    assert genre_normalizer.select_genre_tags(tags) == ("Industrial", "EBM", "Synthpop")


def test_genres_in_prose_avoid_false_friends(genre_normalizer):
    text = "Aus Indien angereist, Programm folgt. Danach Indietropen zwischen Prog, Psych und Pop."
    assert genre_normalizer.genres_from_text(text) == ("Indie", "Prog", "Psych")


@pytest.fixture
def classifier(genre_normalizer) -> EventKindClassifier:
    return EventKindClassifier(genre_normalizer)


def test_categories(classifier):
    assert classifier.from_category_words(["Clubnight", "Party"]) is EventKind.PARTY
    assert classifier.from_category_words(["Konzert"]) is EventKind.CONCERT
    assert classifier.from_category_words(["Theater", "Comedy"]) is EventKind.OTHER
    assert classifier.from_category_words([]) is None


@pytest.mark.parametrize(("genres", "title", "start", "expected"), [
    (("Techno",), "Somnia", EVENING, EventKind.PARTY),
    (("Rock",), "Some Band", EVENING, EventKind.CONCERT),
    (("Reggae",), "Roots Night", LATE, EventKind.PARTY),
    (("Powerpop",), "Band Support; Afterparty with DJ X", EVENING, EventKind.CONCERT),
    ((), "SMUF PARTY", EVENING, EventKind.PARTY),
    (("Pub Quiz",), "Club Quiz", EVENING, EventKind.OTHER),
])
def test_genre_and_title_heuristics(classifier, genres, title, start, expected):
    assert classifier.from_genres_and_title(genres, title, start) is expected
