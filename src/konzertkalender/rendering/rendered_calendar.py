"""The finished calendar image plus where each tappable element sits on it."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PIL import Image

from konzertkalender.domain.event import Event


class RegionKind(Enum):
    EVENT = "event"
    HIDDEN_EVENTS = "hidden_events"  # the "+ N weitere Events" note of a full evening
    FOOTER = "footer"


@dataclass(frozen=True)
class LinkRegion:
    """A full-width horizontal band of the image, in pixels from the top."""

    kind: RegionKind
    top: int
    bottom: int
    event: Event | None = None


@dataclass(frozen=True)
class RenderedCalendar:
    image: Image.Image
    regions: tuple[LinkRegion, ...]
