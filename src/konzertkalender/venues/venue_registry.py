"""Maps the club keys used in config/kalender.toml to their source classes."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

from konzertkalender.venues.bern.cafe_kairo_source import CafeKairoSource
from konzertkalender.venues.bern.cafete_source import CafeteSource
from konzertkalender.venues.bern.dachstock_source import DachstockSource
from konzertkalender.venues.bern.gaskessel_source import GaskesselSource
from konzertkalender.venues.bern.isc_source import IscSource
from konzertkalender.venues.bern.progr_source import ProgrSource
from konzertkalender.venues.bern.roessli_source import RoessliSource
from konzertkalender.venues.fribourg.bad_bonn_source import BadBonnSource
from konzertkalender.venues.fribourg.fri_son_source import FriSonSource
from konzertkalender.venues.fribourg.nouveau_monde_source import NouveauMondeSource
from konzertkalender.venues.source_toolkit import SourceToolkit
from konzertkalender.venues.venue_source import VenueSource

SourceFactory = Callable[[SourceToolkit], VenueSource]

DEFAULT_FACTORIES: Mapping[str, SourceFactory] = {
    "dachstock": DachstockSource,
    "gaskessel": GaskesselSource,
    "isc": IscSource,
    "roessli": RoessliSource,
    "cafete": CafeteSource,
    "cafe_kairo": CafeKairoSource,
    "progr": ProgrSource,
    "bad_bonn": BadBonnSource,
    "fri_son": FriSonSource,
    "nouveau_monde": NouveauMondeSource,
}


class VenueRegistry:
    """Builds the configured venue sources; a new club only needs a class and one entry here."""

    def __init__(self, factories: Mapping[str, SourceFactory] = DEFAULT_FACTORIES) -> None:
        self._factories = dict(factories)

    @property
    def available_keys(self) -> tuple[str, ...]:
        return tuple(self._factories)

    def build(self, keys: Iterable[str], toolkit: SourceToolkit) -> list[VenueSource]:
        requested = list(keys)
        unknown = [key for key in requested if key not in self._factories]
        if unknown:
            raise ValueError(
                f"Unbekannte Clubs in der Konfiguration: {', '.join(unknown)} "
                f"(verfügbar: {', '.join(self.available_keys)})"
            )
        return [self._factories[key](toolkit) for key in requested]
