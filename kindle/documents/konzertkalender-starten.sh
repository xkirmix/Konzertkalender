#!/bin/sh
# Name: Konzertkalender starten
# Author: Konzertkalender
# DontUseFBInk
# Startet den Kalender-Dienst und holt die neueste Ausgabe.
# Danach Power-Taste drücken: im Schlaf zeigt der Kindle den Kalender.

. "${KONZERTKALENDER_INSTALL_HOME:-/mnt/us/konzertkalender}/bin/kalender_lib.sh"

RESULT_WAIT_SECONDS=50

# Waits until the background refresh has recorded a new attempt.
wait_for_refresh() {
    previous_attempt=$1
    result_waited=0
    while [ "$result_waited" -lt "$RESULT_WAIT_SECONDS" ]; do
        [ "$(read_epoch "$LAST_ATTEMPT_FILE")" -gt "$previous_attempt" ] && return 0
        sleep 2
        result_waited=$((result_waited + 2))
    done
    return 1
}

report_refresh() {
    if ! wait_for_refresh "$1"; then
        show_message "Lädt im Hintergrund weiter."
    elif last_refresh_failed; then
        show_message "Download fehlgeschlagen – neuer Versuch in $RETRY_MINUTES Min."
    else
        show_message "Kalender ist aktuell."
    fi
}

clear_screen
show_message "Konzertkalender"
if daemon_is_running; then
    show_message "Dienst läuft bereits."
elif start_daemon; then
    show_message "Dienst gestartet."
else
    show_message "Dienst konnte nicht starten – siehe konzertkalender.log"
fi

previous_attempt=$(read_epoch "$LAST_ATTEMPT_FILE")
start_detached /bin/sh "$INSTALL_HOME/bin/kalender_refresh.sh"
show_message "Neueste Ausgabe wird geladen ..."
report_refresh "$previous_attempt"
show_message "Jetzt Power-Taste drücken."
