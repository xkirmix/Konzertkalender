"""Writes one edition into the output folder that GitHub Pages serves."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from konzertkalender.app.source_status import SourceStatus
from konzertkalender.domain.weekend_program import WeekendProgram
from konzertkalender.publishing.clickable_page_builder import ClickablePageBuilder
from konzertkalender.publishing.program_serializer import ProgramSerializer
from konzertkalender.rendering.footer_info import FooterInfo

IMAGE_FILE = "kalender.png"
PAGE_FILE = "index.html"
DATA_FILE = "kalender.json"
NO_JEKYLL_FILE = ".nojekyll"


class SitePublisher:
    def __init__(self, output_dir: Path, page_builder: ClickablePageBuilder, serializer: ProgramSerializer) -> None:
        self._output_dir = output_dir
        self._page_builder = page_builder
        self._serializer = serializer

    def publish(
        self, image: Image.Image, program: WeekendProgram, footer: FooterInfo, statuses: Sequence[SourceStatus]
    ) -> list[Path]:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        image_path = self._output_dir / IMAGE_FILE
        image.save(image_path, format="PNG", optimize=True)
        page_path = self._output_dir / PAGE_FILE
        page_path.write_text(self._page_builder.build(program, footer), encoding="utf-8")
        data_path = self._output_dir / DATA_FILE
        data = self._serializer.to_dict(program, footer, statuses)
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (self._output_dir / NO_JEKYLL_FILE).touch()
        return [image_path, page_path, data_path]
