#!/bin/sh
# Name: Konzertkalender starten
# Author: Konzertkalender
# DontUseFBInk
# Startet den Kalender-Dienst (oder startet ihn neu) und holt die neueste Ausgabe.
# Danach Power-Taste drücken: im Schlaf zeigt der Kindle den Kalender.

. "${KONZERTKALENDER_INSTALL_HOME:-/mnt/us/konzertkalender}/bin/kalender_lib.sh"

RESULT_WAIT_SECONDS=50

# Waits until a refresh has stored its result (the file is removed before the refresh starts).
wait_for_refresh() {
    result_waited=0
    while [ "$result_waited" -lt "$RESULT_WAIT_SECONDS" ]; do
        [ -f "$LAST_RESULT_FILE" ] && return 0
        sleep 2
        result_waited=$((result_waited + 2))
    done
    return 1
}

report_refresh() {
    if ! wait_for_refresh; then
        show_message "Lädt im Hintergrund weiter."
    elif last_refresh_failed; then
        show_message "Download fehlgeschlagen – neuer Versuch in $RETRY_MINUTES Min."
    else
        show_message "Kalender ist aktuell."
    fi
}

clear_screen
show_message "Konzertkalender"
# A running service is restarted so it picks up changed settings and scripts.
if daemon_is_running; then
    stop_daemon
    started_message="Dienst neu gestartet."
else
    started_message="Dienst gestartet."
fi
if start_daemon; then
    show_message "$started_message"
else
    show_message "Dienst konnte nicht starten – siehe konzertkalender.log"
fi

rm -f "$LAST_RESULT_FILE"
start_detached /bin/sh "$INSTALL_HOME/bin/kalender_refresh.sh"
show_message "Neueste Ausgabe wird geladen ..."
report_refresh
show_message "Jetzt Power-Taste drücken."
