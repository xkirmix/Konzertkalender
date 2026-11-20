#!/bin/sh
# Collects facts for troubleshooting into diagnose.txt on the USB storage. Changes nothing on the
# Kindle (WiFi is switched back to how it was after the network check).

KALENDER_HOME="$(cd "$(dirname "$0")/.." && pwd)"
. "$KALENDER_HOME/bin/kalender_lib.sh"

REPORT_FILE="$INSTALL_HOME/diagnose.txt"
POWERD_NAMES="goingToScreenSaver|outOfScreenSaver|exitingScreenSaver|readyToSuspend|suspending|resuming|wakeupFromSuspend|rtcWakeup|deferSuspend"

section() {
    echo
    echo "=== $* ==="
}

printable_words() {
    if command -v strings > /dev/null 2>&1; then
        strings "$1"
    else
        tr -c 'A-Za-z0-9' '\n' < "$1"
    fi
}

report_system() {
    section "System"
    echo "date:    $(date)"
    echo "date -u: $(date -u)"
    echo "TZ=${TZ:-<leer>}  /etc/TZ: $(cat /etc/TZ 2>&1)"
    hwclock -r 2>&1 | head -2
    id
    uname -a
    cat /etc/prettyversion.txt 2>&1
    df -k /mnt/us /var/local /tmp 2>&1
}

report_jailbreak() {
    section "Jailbreak"
    echo "kmc version: $(cat /var/local/kmc/version 2>&1)"
    ls -la /var/local/kmc/bin/ /mnt/us/libkh/bin/ 2>&1 | head -30
    ls -la /usr/bin/otaupd* /usr/bin/otav3* 2>&1
    echo "fbink: ${FBINK:-keins}"
}

report_tools() {
    section "Werkzeuge"
    for tool in setsid nohup curl eips mkfifo lipc-wait-event lipc-probe sqlite3 dbus-monitor strings; do
        echo "$tool: $(command -v "$tool" || echo fehlt)"
    done
    echo "--- lipc-wait-event ohne Argumente:"
    lipc-wait-event 2>&1 | head -20
}

report_powerd() {
    section "powerd"
    lipc-get-prop com.lab126.powerd status 2>&1
    echo "--- Eigenschaften:"
    lipc-probe -v com.lab126.powerd 2>&1 | head -80
    echo "--- Ereignisnamen im Programm:"
    powerd_binary=$(command -v powerd || echo /usr/bin/powerd)
    printable_words "$powerd_binary" | grep -o -E "$POWERD_NAMES" | sort | uniq -c
}

report_browser() {
    section "Browser"
    sqlite3 /var/local/appreg.db \
        "select handlerId, name, value from properties where handlerId like '%browser%';" 2>&1 | head -40
    echo "--- Aufrufe im System:"
    grep -r -h -o "app://com.lab126.browser[^\"' <]*" /usr/share/webkit-1.0 /etc /usr/bin /usr/sbin \
        2> /dev/null | sort | uniq | head -20
}

report_network() {
    section "Netzwerk"
    echo "wirelessEnable: $(lipc-get-prop com.lab126.cmd wirelessEnable 2>&1)"
    echo "cmState vorher: $(lipc-get-prop com.lab126.wifid cmState 2>&1)"
    if ensure_wifi; then
        ifconfig wlan0 2>&1 | head -3
        curl -sS -o /dev/null -w "Seite: HTTP %{http_code}\n" --max-time 30 "$PAGE_URL" 2>&1
        curl -sS -o /dev/null -w "Bild: HTTP %{http_code}\n" --max-time 30 "$IMAGE_URL" 2>&1
    else
        echo "WLAN nicht verbunden: $(lipc-get-prop com.lab126.wifid cmState 2>&1)"
    fi
    restore_wifi
}

report_service() {
    section "Konzertkalender"
    if daemon_is_running; then
        echo "Dienst läuft: $(cat "$PID_FILE")"
    else
        echo "Dienst läuft nicht"
    fi
    ls -la "$DATA_DIR" 2>&1
    tail -n 60 "$LOG_FILE" 2>&1
}

{
    report_system
    report_jailbreak
    report_tools
    report_powerd
    report_browser
    report_network
    report_service
} > "$REPORT_FILE" 2>&1

MESSAGE_ROW=12
show_message "Diagnose fertig: konzertkalender/diagnose.txt"
