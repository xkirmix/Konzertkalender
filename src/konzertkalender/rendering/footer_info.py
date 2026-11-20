"""What the footer line reports: when the edition was made and which clubs could be read."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FooterInfo:
    generated_at: datetime
    healthy_venues: tuple[str, ...]
    failed_venues: tuple[str, ...]

    @property
    def summary(self) -> str:
        total = len(self.healthy_venues) + len(self.failed_venues)
        read = f"{len(self.healthy_venues)}/{total} Clubs gelesen"
        return f"{read} · keine Daten: {', '.join(self.failed_venues)}" if self.failed_venues else read
