#!/bin/sh
# Konzertkalender service: paints the calendar over the sleep screen, wakes the Kindle via the RTC
# when the next edition is due, and opens the clickable page when the user wakes the Kindle.

KALENDER_HOME="$(cd "$(dirname "$0")/.." && pwd)"
. "$KALENDER_HOME/bin/kalender_lib.sh"

EVENT_FIFO="$TMP_DIR/konzertkalender.events"
POWERD_EVENTS="goingToScreenSaver,outOfScreenSaver,readyToSuspend,wakeupFromSuspend"
SCREENSAVER_SETTLE_SECONDS="${SCREENSAVER_SETTLE_SECONDS:-2}"

start_event_listener() {
    rm -f "$EVENT_FIFO"
    mkfifo "$EVENT_FIFO"
    lipc-wait-event -m -s 0 com.lab126.powerd "$POWERD_EVENTS" > "$EVENT_FIFO" &
    LISTENER_PID=$!
}

# Troubleshooting aid (DEBUG_EVENTS=1): logs every raw powerd signal seen on the system bus.
start_debug_recorder() {
    DEBUG_PID=""
    [ "$DEBUG_EVENTS" = "1" ] && command -v dbus-monitor > /dev/null 2>&1 || return 0
    dbus-monitor --system "type='signal',interface='com.lab126.powerd'" 2>&1 |
        while read -r bus_line; do
            case "$bus_line" in
                *member=*) log "dbus: ${bus_line##*member=}" ;;
            esac
        done &
    DEBUG_PID=$!
}

shutdown_service() {
    kill "$LISTENER_PID" $DEBUG_PID 2> /dev/null
    rm -f "$EVENT_FIFO" "$PID_FILE"
    log "Dienst beendet"
    exit 0
}

# The Kindle draws its own sleep screen first; we paint the calendar over it.
paint_sleep_screen() {
    sleep "$SCREENSAVER_SETTLE_SECONDS"
    show_image && draw_battery_warning
}

schedule_wakeup() {
    wakeup_seconds=$(seconds_until_refresh)
    if lipc-set-prop -i com.lab126.powerd rtcWakeup "$wakeup_seconds"; then
        log "Schlaf – Wecker in $((wakeup_seconds / 60)) Min."
    else
        log "Wecker konnte nicht gestellt werden"
    fi
}

refresh_after_wakeup() {
    refresh_is_due || return 0
    log "Aufgewacht – hole neue Ausgabe"
    if refresh_edition; then
        show_image && draw_battery_warning
    fi
}

handle_event() {
    case "$1" in
        goingToScreenSaver) paint_sleep_screen ;;
        readyToSuspend) schedule_wakeup ;;
        wakeupFromSuspend) refresh_after_wakeup ;;
        outOfScreenSaver) [ "$OPEN_PAGE_ON_WAKE" = "1" ] && open_page ;;
    esac
}

start_event_listener
start_debug_recorder
echo "$$ $LISTENER_PID $DEBUG_PID" > "$PID_FILE"
trap shutdown_service TERM INT
log "Dienst gestartet (PID $$, Ereignisse von PID $LISTENER_PID)"
use_start_image_if_missing

while read -r powerd_event _; do
    log "Ereignis: $powerd_event"
    handle_event "$powerd_event"
done < "$EVENT_FIFO"

log "Ereignisquelle beendet"
shutdown_service
