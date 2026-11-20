"""Writes one edition into the output folder that GitHub Pages serves.

  kalender.png  the sleep-screen image the Kindle downloads
  index.html    the same image as a tappable page (opened when the Kindle wakes up)
  liste.html    all events as a plain list (reached from the image's footer and "+ N weitere")
  kalender.json the same data, machine-readable
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.publishing.calendar_page_builder import CalendarPageBuilder
from konzertkalender.publishing.event_list_page_builder import EventListPageBuilder
from konzertkalender.publishing.program_serializer import ProgramSerializer
from konzertkalender.rendering.footer_info import FooterInfo
from konzertkalender.rendering.rendered_calendar import RenderedCalendar

IMAGE_FILE = "kalender.png"
PAGE_FILE = "index.html"
LIST_FILE = "liste.html"
DATA_FILE = "kalender.json"
NO_JEKYLL_FILE = ".nojekyll"
IMAGE_VERSION_LENGTH = 10


class SitePublisher:
    def __init__(
        self,
        output_dir: Path,
        calendar_page: CalendarPageBuilder,
        list_page: EventListPageBuilder,
        serializer: ProgramSerializer,
    ) -> None:
        self._output_dir = output_dir
        self._calendar_page = calendar_page
        self._list_page = list_page
        self._serializer = serializer

    def publish(
        self, calendar: RenderedCalendar, program: WeekendProgram, footer: FooterInfo, statuses: Sequence[SourceStatus]
    ) -> list[Path]:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        image_path = self._output_dir / IMAGE_FILE
        calendar.image.save(image_path, format="PNG", optimize=True)
        # A new address for every new image, so no browser shows a cached old edition.
        version = hashlib.sha1(image_path.read_bytes()).hexdigest()[:IMAGE_VERSION_LENGTH]
        page_path = self._output_dir / PAGE_FILE
        page_path.write_text(
            self._calendar_page.build(calendar, program, f"{IMAGE_FILE}?v={version}", LIST_FILE), encoding="utf-8"
        )
        list_path = self._output_dir / LIST_FILE
        list_path.write_text(self._list_page.build(program, footer), encoding="utf-8")
        data_path = self._output_dir / DATA_FILE
        data = self._serializer.to_dict(program, footer, statuses)
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self._output_dir / NO_JEKYLL_FILE).touch()
        return [image_path, page_path, list_path, data_path]
