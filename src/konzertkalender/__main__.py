"""Command line: `python -m konzertkalender [--ausgabe docs] [--datum 2026-11-23]`."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from konzertkalender.app.app_config import DEFAULT_CONFIG_PATH, AppConfig
from konzertkalender.app.application_assembler import ApplicationAssembler
from konzertkalender.publishing.text_summary import TextSummaryWriter
from konzertkalender.rendering.event_text_formatter import EventTextFormatter


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="konzertkalender",
        description="Erstellt den Wochenend-Kalender (Bild für den Kindle + klickbare Webseite).",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Konfigurationsdatei")
    parser.add_argument("--ausgabe", type=Path, default=Path("docs"), help="Zielordner (Standard: docs)")
    parser.add_argument(
        "--datum", type=date.fromisoformat, default=None,
        help="Bezugsdatum JJJJ-MM-TT; bestimmt das Wochenende (Standard: heute)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = AppConfig.load(arguments.config)
    zone = ZoneInfo(config.timezone)
    assembler = ApplicationAssembler(config, arguments.ausgabe, clock=lambda: datetime.now(zone))
    report = assembler.build_coordinator().run(arguments.datum)
    print(TextSummaryWriter(EventTextFormatter()).render(report.program, report.statuses))
    for written in report.written_files:
        print(f"geschrieben: {written}")
    return 1 if report.all_sources_failed else 0


if __name__ == "__main__":
    sys.exit(main())
