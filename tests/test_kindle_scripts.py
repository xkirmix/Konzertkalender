"""The Kindle-side shell scripts, run under busybox ash against a stand-in Kindle."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fake_kindle import BUSYBOX, PNG_BYTES, FakeKindle

pytestmark = pytest.mark.skipif(BUSYBOX is None, reason="busybox ist nicht installiert")

TWELVE_HOURS = 12 * 3600
ONE_HOUR = 3600


@pytest.fixture
def kindle(tmp_path: Path) -> FakeKindle:
    return FakeKindle(tmp_path)


def refresh_result(kindle: FakeKindle) -> str:
    completed = kindle.run_with_library('refresh_edition; echo "result=$?"')
    match = re.search(r"result=(\d)", completed.stdout)
    assert match, completed.stderr
    return match.group(1)


def seconds_until_refresh(kindle: FakeKindle) -> int:
    return int(kindle.run_with_library("seconds_until_refresh").stdout.strip())


def test_refresh_stores_new_image_then_reports_unchanged(kindle: FakeKindle) -> None:
    assert refresh_result(kindle) == "0"
    assert kindle.image_file.read_bytes() == PNG_BYTES
    assert refresh_result(kindle) == "1"


def test_refresh_keeps_previous_image_when_answer_is_not_png(kindle: FakeKindle) -> None:
    refresh_result(kindle)
    kindle.serve(b"<html>404 - Not Found</html>")
    assert refresh_result(kindle) == "2"
    assert kindle.image_file.read_bytes() == PNG_BYTES
    assert "kein PNG" in (kindle.data_dir / "konzertkalender.log").read_text()


def test_next_wakeup_after_success_is_refresh_hours(kindle: FakeKindle) -> None:
    refresh_result(kindle)
    assert TWELVE_HOURS - 10 <= seconds_until_refresh(kindle) <= TWELVE_HOURS


def test_next_wakeup_after_failure_is_retry_minutes(kindle: FakeKindle) -> None:
    kindle.serve(b"not an image")
    refresh_result(kindle)
    assert ONE_HOUR - 10 <= seconds_until_refresh(kindle) <= ONE_HOUR


def test_refresh_without_wifi_fails_and_switches_wifi_back_off(tmp_path: Path) -> None:
    kindle = FakeKindle(tmp_path, wifi_state="NA")
    kindle.run_with_library("WIFI_TIMEOUT_SECONDS=2; refresh_edition")
    calls = kindle.calls()
    assert "lipc-set-prop com.lab126.cmd wirelessEnable 1" in calls
    assert calls[-1] == "lipc-set-prop com.lab126.cmd wirelessEnable 0"
    assert not kindle.image_file.exists()


def test_daemon_paints_sleep_screen_and_sets_rtc_wakeup(kindle: FakeKindle) -> None:
    refresh_result(kindle)
    kindle.powerd_events(["goingToScreenSaver", "readyToSuspend"])
    completed = kindle.run_daemon()
    assert completed.returncode == 0, completed.stderr
    calls = kindle.calls()
    assert f"eips -f -g {kindle.image_file}" in calls
    wakeups = [call for call in calls if "rtcWakeup" in call]
    assert len(wakeups) == 1
    assert TWELVE_HOURS - 10 <= int(wakeups[0].split()[-1]) <= TWELVE_HOURS


def test_daemon_shows_start_image_until_first_download(kindle: FakeKindle) -> None:
    (kindle.install_home / "startbild.png").write_bytes(PNG_BYTES)
    kindle.powerd_events(["goingToScreenSaver"])
    kindle.run_daemon()
    assert kindle.image_file.read_bytes() == PNG_BYTES
    assert f"eips -f -g {kindle.image_file}" in kindle.calls()


def test_daemon_logs_every_event(kindle: FakeKindle) -> None:
    kindle.powerd_events(["readyToSuspend", "wakeupFromSuspend"])
    kindle.run_daemon()
    log = (kindle.data_dir / "konzertkalender.log").read_text()
    assert "Ereignis: readyToSuspend" in log
    assert "Ereignis: wakeupFromSuspend" in log


def test_daemon_opens_page_when_user_wakes_the_kindle(kindle: FakeKindle) -> None:
    kindle.powerd_events(["outOfScreenSaver"])
    kindle.run_daemon()
    assert any(
        call.startswith("lipc-set-prop com.lab126.appmgrd start app://com.lab126.browser")
        for call in kindle.calls()
    )


def test_daemon_skips_download_on_wakeup_when_not_due(kindle: FakeKindle) -> None:
    refresh_result(kindle)
    attempt_before = (kindle.data_dir / "last_attempt").read_text()
    kindle.powerd_events(["wakeupFromSuspend"])
    kindle.run_daemon()
    assert (kindle.data_dir / "last_attempt").read_text() == attempt_before


def test_daemon_downloads_on_wakeup_when_due(kindle: FakeKindle) -> None:
    kindle.powerd_events(["wakeupFromSuspend"])
    kindle.run_daemon()
    assert kindle.image_file.read_bytes() == PNG_BYTES
    assert f"eips -f -g {kindle.image_file}" in kindle.calls()


def test_start_scriptlet_starts_restarts_and_stop_scriptlet_stops(kindle: FakeKindle) -> None:
    kindle.keep_listening()
    kindle.run_scriptlet("konzertkalender-starten.sh")
    kindle.run_scriptlet("konzertkalender-starten.sh")
    kindle.run_scriptlet("konzertkalender-stoppen.sh")
    messages = kindle.screen_messages()
    assert "Dienst gestartet." in messages
    assert "Dienst neu gestartet." in messages
    assert "Kalender ist aktuell." in messages
    assert messages[-1] == "Dienst gestoppt. Der Kindle ist wieder normal."
    assert not (kindle.tmp_dir / "konzertkalender.pid").exists()


def test_timestamp_in_the_future_makes_refresh_due(kindle: FakeKindle) -> None:
    refresh_result(kindle)
    future = int((kindle.data_dir / "last_attempt").read_text()) + 7 * 3600
    (kindle.data_dir / "last_attempt").write_text(f"{future}\n")
    (kindle.data_dir / "last_success").write_text(f"{future}\n")
    completed = kindle.run_with_library('refresh_is_due && echo due; seconds_until_refresh')
    assert completed.stdout.split() == ["due", "120"]


def test_tick_refreshes_while_kindle_never_suspends(kindle: FakeKindle) -> None:
    kindle.tick_seconds = 1
    kindle.keep_listening()
    service = kindle.start_daemon_in_background()
    try:
        assert kindle.wait_until(lambda: f"eips -f -g {kindle.image_file}" in kindle.calls())
        assert kindle.image_file.read_bytes() == PNG_BYTES
    finally:
        kindle.stop_services()
        service.wait(timeout=10)


def test_new_edition_is_not_painted_while_kindle_is_in_use(kindle: FakeKindle) -> None:
    kindle.set_powerd_state("active")
    kindle.powerd_events(["wakeupFromSuspend"])
    kindle.run_daemon()
    assert kindle.image_file.read_bytes() == PNG_BYTES
    assert f"eips -f -g {kindle.image_file}" not in kindle.calls()


def test_service_restarts_itself_after_an_update_was_copied(kindle: FakeKindle) -> None:
    runtime_home = kindle.install_runtime_copy()
    config = kindle.install_home / "konzertkalender.conf"
    config.write_text(config.read_text() + "# neue Einstellung\n")
    kindle.powerd_events(["goingToScreenSaver"])
    kindle.run_daemon(home=runtime_home)
    assert kindle.wait_until(lambda: kindle.log_text().count("Dienst gestartet") == 2)
    assert kindle.wait_until(lambda: "Ereignisquellen beendet" in kindle.log_text())
    assert kindle.log_text().count("Neue Version gefunden") == 1
    assert (runtime_home / "konzertkalender.conf").read_text() == config.read_text()
