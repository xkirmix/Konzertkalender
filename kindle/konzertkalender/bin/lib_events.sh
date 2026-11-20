#!/bin/sh
# The service's event sources. Each writes one line per event into a FIFO that the service reads:
#   - powerd signals (sleep screen, suspend, wakeup) via lipc-wait-event,
#   - a periodic "tick" for when the Kindle never suspends (e.g. while it hangs on the charger),
#   - with DEBUG_EVENTS=1, a recorder that logs every raw powerd signal (troubleshooting only).

EVENT_FIFO="$TMP_DIR/konzertkalender.events"
POWERD_EVENTS="goingToScreenSaver,outOfScreenSaver,readyToSuspend,wakeupFromSuspend"
TICK_SECONDS="${TICK_SECONDS:-1800}"
EVENT_SOURCE_PIDS=""

start_powerd_listener() {
    lipc-wait-event -m com.lab126.powerd "$POWERD_EVENTS" > "$EVENT_FIFO" &
    EVENT_SOURCE_PIDS="$EVENT_SOURCE_PIDS $!"
}

# sleep does not count time spent suspended, so ticks only matter while the Kindle stays awake.
start_ticker() {
    [ "$TICK_SECONDS" -gt 0 ] || return 0
    (while sleep "$TICK_SECONDS"; do echo tick; done) > "$EVENT_FIFO" &
    EVENT_SOURCE_PIDS="$EVENT_SOURCE_PIDS $!"
}

start_debug_recorder() {
    [ "$DEBUG_EVENTS" = "1" ] && command -v dbus-monitor > /dev/null 2>&1 || return 0
    dbus-monitor --system "type='signal',interface='com.lab126.powerd'" 2>&1 |
        while read -r bus_line; do
            case "$bus_line" in
                *member=*) log "dbus: ${bus_line##*member=}" ;;
            esac
        done &
    EVENT_SOURCE_PIDS="$EVENT_SOURCE_PIDS $!"
}

start_event_sources() {
    rm -f "$EVENT_FIFO"
    mkfifo "$EVENT_FIFO"
    start_powerd_listener
    start_ticker
    start_debug_recorder
}

stop_event_sources() {
    if [ -n "$EVENT_SOURCE_PIDS" ]; then
        # shellcheck disable=SC2086  # a list of PIDs
        kill $EVENT_SOURCE_PIDS 2> /dev/null
    fi
    rm -f "$EVENT_FIFO"
}
