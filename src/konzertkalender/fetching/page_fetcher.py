"""Downloading web pages politely; injected into venue sources so they can be tested offline."""

from __future__ import annotations

import time
from typing import Protocol

import requests

DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64)"


class PageFetchError(RuntimeError):
    """Raised when a page could not be downloaded after all retries."""


class PageFetcher(Protocol):
    def fetch_text(self, url: str) -> str:
        """Returns the decoded body of the page at `url` or raises PageFetchError."""
        ...


class HttpPageFetcher:
    """Fetches pages with a timeout, a few retries and a short pause after every request."""

    def __init__(
        self,
        session: requests.Session | None = None,
        timeout_seconds: float = 25.0,
        retries: int = 2,
        pause_seconds: float = 1.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self._session = session or requests.Session()
        self._session.headers["User-Agent"] = user_agent
        self._timeout_seconds = timeout_seconds
        self._retries = retries
        self._pause_seconds = pause_seconds

    def fetch_text(self, url: str) -> str:
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            try:
                return self._download(url)
            except requests.RequestException as error:
                last_error = error
                time.sleep(self._pause_seconds * (attempt + 1))
        raise PageFetchError(f"{url}: {last_error}") from last_error

    def _download(self, url: str) -> str:
        response = self._session.get(url, timeout=self._timeout_seconds)
        response.raise_for_status()
        if "charset" not in response.headers.get("Content-Type", "").lower():
            response.encoding = response.apparent_encoding or "utf-8"
        time.sleep(self._pause_seconds)
        return response.text
