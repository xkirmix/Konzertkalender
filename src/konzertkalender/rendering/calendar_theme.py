"""Screen size, colors, fonts and base text sizes of the calendar image."""

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
    """Defaults fit a Kindle Paperwhite 4 in portrait orientation (300 ppi, 16 gray levels)."""

    width: int = 1072
    height: int = 1448
    margin: int = 44
    fonts: FontFiles = field(default_factory=FontFiles)
    ink: int = 0
    secondary_ink: int = 70
    muted_ink: int = 120
    paper: int = 255
    title_size: int = 54
    subtitle_size: int = 28
    heading_size: int = 29
    time_size: int = 31
    event_title_size: int = 31
    meta_size: int = 24
    footer_size: int = 20
    max_title_lines: int = 2
    max_scale: float = 1.0
    min_stacked_scale: float = 0.8  # below this, one line per event reads better than two small lines
    min_scale: float = 0.62
    scale_step: float = 0.04
