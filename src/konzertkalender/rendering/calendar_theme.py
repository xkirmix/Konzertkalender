"""Screen size, colors, fonts, base text sizes and spacing of the calendar image."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

FONT_DIRECTORY = Path(__file__).resolve().parent.parent / "assets" / "fonts"


@dataclass(frozen=True)
class FontFiles:
    regular: Path = FONT_DIRECTORY / "Inter-Regular.otf"
    semibold: Path = FONT_DIRECTORY / "Inter-SemiBold.otf"
    bold: Path = FONT_DIRECTORY / "Inter-Bold.otf"
    heavy: Path = FONT_DIRECTORY / "Inter-ExtraBold.otf"


@dataclass(frozen=True)
class CalendarTheme:
    """Defaults fit a Kindle Paperwhite 4 in portrait orientation (300 ppi, 16 gray levels).

    Sizes and gaps are given at scale 1.0; the layout scales them down (not below `min_scale`) when
    a weekend has many events.
    """

    width: int = 1072
    height: int = 1448
    margin: int = 40
    fonts: FontFiles = field(default_factory=FontFiles)
    # gray levels: 0 = black, 255 = white; e-ink needs strong contrast for small text
    ink: int = 0
    secondary_ink: int = 50
    venue_ink: int = 0
    details_ink: int = 55
    muted_ink: int = 110
    paper: int = 255
    footer_size: int = 20
    # event list
    heading_size: int = 31
    time_size: int = 34
    event_title_size: int = 34
    meta_size: int = 30
    heading_height_factor: float = 1.3
    row_gap: int = 10
    section_gap: int = 14
    inline_gap: int = 18
    max_title_lines: int = 2
    max_scale: float = 1.0
    min_stacked_scale: float = 0.8  # below this, one line per event reads better than two small lines
    min_scale: float = 0.8  # never smaller: the fullest evenings show "+ N weitere Events" instead
    scale_step: float = 0.04
