"""A stand-in Kindle for running the Kindle-side shell scripts under busybox ash on a computer.

It copies kindle/konzertkalender into a temporary folder, points the image address at a local file
and puts small fake versions of the Kindle tools (lipc-*, eips) first on PATH. The fakes record
every call so tests can check what the scripts asked the Kindle to do.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KINDLE_SOURCE = PROJECT_ROOT / "kindle" / "konzertkalender"
SCRIPTLETS = PROJECT_ROOT / "kindle" / "documents"
BUSYBOX = shutil.which("busybox")
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + bytes(32)  # the scripts only check the PNG signature


class FakeKindle:
    """Temporary install, data and tmp folders plus recording fakes for the Kindle tools."""

    def __init__(self, root: Path, wifi_state: str = "CONNECTED") -> None:
        self.install_home = root / "us" / "konzertkalender"
        self.data_dir = root / "var-local"
        self.tmp_dir = root / "tmp"
        self.fake_bin = root / "fake-bin"
        self.calls_file = root / "calls.log"
        self.events_file = root / "powerd-events.txt"
        self.served_image = root / "served" / "kalender.png"
        self.keep_listening_flag = root / "keep-listening"
        shutil.copytree(KINDLE_SOURCE, self.install_home)
        for folder in (self.data_dir, self.tmp_dir, self.fake_bin, self.served_image.parent):
            folder.mkdir(parents=True)
        self.serve(PNG_BYTES)
        self.powerd_events([])
        self._point_image_url_at_served_file()
        self._write_fake_tools(wifi_state)

    @property
    def image_file(self) -> Path:
        return self.data_dir / "kalender.png"

    def serve(self, content: bytes) -> None:
        self.served_image.write_bytes(content)

    def powerd_events(self, events: list[str]) -> None:
        self.events_file.write_text("".join(f"{event} 0\n" for event in events))

    def calls(self) -> list[str]:
        if not self.calls_file.exists():
            return []
        return self.calls_file.read_text().splitlines()

    def run_with_library(self, commands: str) -> subprocess.CompletedProcess[str]:
        library = self.install_home / "bin" / "kalender_lib.sh"
        return self._run_ash(["-c", f'. "{library}"\n{commands}'])

    def keep_listening(self) -> None:
        """Lets the fake event source stay open, so a started service keeps running."""
        self.keep_listening_flag.touch()

    def run_scriptlet(self, file_name: str) -> subprocess.CompletedProcess[str]:
        return self._run_ash([str(SCRIPTLETS / file_name)])

    def screen_messages(self) -> list[str]:
        prefix = "eips 1 "
        return [call.split(" ", 3)[3] for call in self.calls() if call.startswith(prefix)]

    def run_daemon(self) -> subprocess.CompletedProcess[str]:
        return self._run_ash([str(self.install_home / "bin" / "kalender_daemon.sh")])

    def _run_ash(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        assert BUSYBOX is not None
        return subprocess.run(
            [BUSYBOX, "ash", *arguments],
            env=self._environment(),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )

    def _environment(self) -> dict[str, str]:
        return {
            "PATH": f"{self.fake_bin}{os.pathsep}{os.environ.get('PATH', '')}",
            "HOME": str(self.tmp_dir),
            "KONZERTKALENDER_INSTALL_HOME": str(self.install_home),
            "KONZERTKALENDER_DATA_DIR": str(self.data_dir),
            "KONZERTKALENDER_TMP_DIR": str(self.tmp_dir),
            "SCREENSAVER_SETTLE_SECONDS": "0",
        }

    def _point_image_url_at_served_file(self) -> None:
        config_file = self.install_home / "konzertkalender.conf"
        config = re.sub(
            r'^IMAGE_URL=".*"$',
            f'IMAGE_URL="file://{self.served_image}"',
            config_file.read_text(),
            flags=re.MULTILINE,
        )
        config_file.write_text(config)

    def _write_fake_tools(self, wifi_state: str) -> None:
        record = f'echo "$(basename "$0") $*" >> "{self.calls_file}"'
        self._write_tool("lipc-set-prop", record)
        self._write_tool("eips", record)
        self._write_tool(
            "lipc-get-prop",
            f'{record}\ncase "$2" in cmState) echo "{wifi_state}" ;; battLevel) echo 80 ;; esac',
        )
        self._write_tool(
            "lipc-wait-event",
            f'{record}\ncat "{self.events_file}"\n[ -f "{self.keep_listening_flag}" ] && exec sleep 20',
        )

    def _write_tool(self, name: str, body: str) -> None:
        tool = self.fake_bin / name
        tool.write_text(f"#!/bin/sh\n{body}\n")
        tool.chmod(0o755)
