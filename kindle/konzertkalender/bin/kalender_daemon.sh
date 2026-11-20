#!/bin/sh
# Konzertkalender service: paints the calendar over the sleep screen, fetches the next edition when it
# is due (after an RTC wakeup, or on a periodic tick when the Kindle never suspends) and opens the
# clickable page when the user wakes the Kindle.

KALENDER_HOME="$(cd "$(dirname "$0")/.." && pwd)"
. "$KALENDER_HOME/bin/kalender_lib.sh"

SCREENSAVER_SETTLE_SECONDS="${SCREENSAVER_SETTLE_SECONDS:-2}"

shutdown_service() {
    stop_event_sources
    rm -f "$PID_FILE"
    log "Dienst beendet"
    exit 0
}

restart_if_installation_changed() {
    installation_changed || return 0
    log "Neue Version gefunden – Dienst startet neu"
    stop_event_sources
    rm -f "$PID_FILE"
    start_daemon
    exit 0
}

# The Kindle draws its own sleep screen first; we paint the calendar over it.
paint_sleep_screen() {
    sleep "$SCREENSAVER_SETTLE_SECONDS"
    show_image && draw_battery_warning
}

schedule_wakeup() {
    wakeup_seconds=$(seconds_until_refresh)
    if set_rtc_wakeup "$wakeup_seconds"; then
        log "Schlaf – Wecker in $((wakeup_seconds / 60)) Min."
    else
        log "Wecker konnte nicht gestellt werden"
    fi
}

# Never paints over the screen while somebody is using the Kindle.
refresh_if_due() {
    refresh_is_due || return 0
    log "Neue Ausgabe fällig"
    if refresh_edition && ! kindle_in_use; then
        show_image && draw_battery_warning
    fi
}

handle_event() {
    case "$1" in
        goingToScreenSaver) paint_sleep_screen; restart_if_installation_changed ;;
        readyToSuspend) schedule_wakeup ;;
        wakeupFromSuspend) refresh_if_due ;;
        outOfScreenSaver) [ "$OPEN_PAGE_ON_WAKE" = "1" ] && open_page ;;
        tick) refresh_if_due; restart_if_installation_changed ;;
    esac
}

start_event_sources
echo "$$$EVENT_SOURCE_PIDS" > "$PID_FILE"
trap shutdown_service TERM INT
log "Dienst gestartet (PID $$)"
use_start_image_if_missing

while read -r event_name _; do
    [ "$event_name" = "tick" ] || log "Ereignis: $event_name"
    handle_event "$event_name"
done < "$EVENT_FIFO"

log "Ereignisquellen beendet"
shutdown_service
