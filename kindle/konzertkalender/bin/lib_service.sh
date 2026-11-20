#!/bin/sh
# Starting and stopping the background service. It runs detached from the library script that
# launched it (the Kindle kills a library script as soon as the user leaves it), from a copy in RAM.

PID_FILE="$TMP_DIR/konzertkalender.pid"

start_detached() {
    if command -v setsid > /dev/null 2>&1; then
        setsid "$@" < /dev/null > /dev/null 2>&1 &
    else
        nohup "$@" < /dev/null > /dev/null 2>&1 &
    fi
}

prepare_runtime_copy() {
    rm -rf "$RUNTIME_HOME"
    mkdir -p "$RUNTIME_HOME" &&
        cp -r "$INSTALL_HOME/bin" "$INSTALL_HOME/konzertkalender.conf" "$RUNTIME_HOME/"
}

start_daemon() {
    if ! prepare_runtime_copy; then
        log "Konnte Dienst nicht nach $RUNTIME_HOME kopieren"
        return 1
    fi
    start_detached /bin/sh "$RUNTIME_HOME/bin/kalender_daemon.sh"
}

daemon_is_running() {
    [ -f "$PID_FILE" ] || return 1
    daemon_pid=$(cut -d' ' -f1 "$PID_FILE")
    [ -n "$daemon_pid" ] && kill -0 "$daemon_pid" 2> /dev/null
}

stop_daemon() {
    [ -f "$PID_FILE" ] || return 1
    # shellcheck disable=SC2046  # the file holds two PIDs: service and event listener
    kill $(cat "$PID_FILE") 2> /dev/null
    rm -f "$PID_FILE"
    log "Dienst gestoppt"
    return 0
}
