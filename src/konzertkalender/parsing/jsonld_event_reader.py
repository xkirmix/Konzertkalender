"""Extracting schema.org Event objects from JSON-LD blocks embedded in HTML pages."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Any

from bs4 import BeautifulSoup


class JsonLdEventReader:
    """Reads all objects whose @type ends with "Event" (Event, MusicEvent, ...) from a page."""

    def read_events(self, html: str) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        events: list[dict[str, Any]] = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                payload = json.loads(script.string or script.get_text() or "")
            except json.JSONDecodeError:
                continue
            events.extend(self._collect_events(payload))
        return events

    def _collect_events(self, node: Any) -> Iterator[dict[str, Any]]:
        if isinstance(node, list):
            for item in node:
                yield from self._collect_events(item)
        elif isinstance(node, dict):
            if self._is_event(node):
                yield node
                return
            for value in node.values():
                if isinstance(value, (list, dict)):
                    yield from self._collect_events(value)

    @staticmethod
    def _is_event(node: dict[str, Any]) -> bool:
        declared = node.get("@type", "")
        types = declared if isinstance(declared, list) else [declared]
        return any(str(kind).endswith("Event") for kind in types)
