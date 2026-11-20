"""Loading config/kalender.toml into a typed configuration object."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from konzertkalender.domain.event import EventKind

DEFAULT_CONFIG_PATH = Path("config/kalender.toml")


@dataclass(frozen=True)
class AppConfig:
    title: str
    timezone: str
    evening_start_hour: int
    night_end_hour: int
    included_kinds: frozenset[EventKind]
    venue_keys: tuple[str, ...]
    genre_file: Path

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "AppConfig":
        with path.open("rb") as handle:
            settings = tomllib.load(handle)["kalender"]
        return cls(
            title=settings.get("titel", "Konzerte"),
            timezone=settings.get("zeitzone", "Europe/Zurich"),
            evening_start_hour=int(settings.get("abend_ab_stunde", 17)),
            night_end_hour=int(settings.get("nacht_bis_stunde", 5)),
            included_kinds=frozenset(EventKind.from_config_value(kind) for kind in settings.get("arten", ["konzert"])),
            venue_keys=tuple(settings.get("clubs", ())),
            genre_file=path.parent / settings.get("genre_datei", "genres.toml"),
        )
