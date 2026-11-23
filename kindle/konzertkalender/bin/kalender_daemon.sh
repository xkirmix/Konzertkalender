#!/bin/sh
# Konzertkalender service: paints the calendar over the sleep screen (and again whenever Amazon's lock
# screen has covered it), fetches the next edition when it is due (after an RTC wakeup, or on a
# periodic tick when the Kindle never suspends) and opens the clickable page when the user wakes it.

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
    paint_calendar
}

# After a short wakeup the Kindle may redraw its lock screen; never while somebody uses it.
guard_sleep_screen() {
    kindle_in_use || repaint_if_covered
}

# powerd asks several times before it really suspends; the wakeup is logged once.
schedule_wakeup() {
    wakeup_seconds=$(seconds_until_refresh)
    if ! set_rtc_wakeup "$wakeup_seconds"; then
        log "Wecker konnte nicht gestellt werden"
        return 1
    fi
    wakeup_minutes=$((wakeup_seconds / 60))
    if [ "$wakeup_minutes" != "$LAST_LOGGED_WAKEUP" ]; then
        log "Schlaf – Wecker in $wakeup_minutes Min."
        LAST_LOGGED_WAKEUP=$wakeup_minutes
    fi
}

after_wakeup() {
    refresh_if_due
    sleep "$SCREENSAVER_SETTLE_SECONDS"
    guard_sleep_screen
}

# Never paints over the screen while somebody is using the Kindle.
refresh_if_due() {
    refresh_is_due || return 0
    log "Neue Ausgabe fällig"
    if refresh_edition && ! kindle_in_use; then
        paint_calendar
    fi
}

handle_event() {
    case "$1" in
        goingToScreenSaver) paint_sleep_screen; restart_if_installation_changed ;;
        readyToSuspend) schedule_wakeup; guard_sleep_screen ;;
        wakeupFromSuspend) after_wakeup ;;
        outOfScreenSaver) [ "$OPEN_PAGE_ON_WAKE" = "1" ] && open_page ;;
        tick) refresh_if_due; guard_sleep_screen; restart_if_installation_changed ;;
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
