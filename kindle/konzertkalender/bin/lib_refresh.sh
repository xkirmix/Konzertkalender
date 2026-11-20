#!/bin/sh
# One refresh run: WiFi on, download, WiFi back to how it was, remember the outcome.
# A lock keeps the service and a tapped library script from refreshing at the same time.

REFRESH_LOCK_DIR="$TMP_DIR/konzertkalender.refresh.lock"

acquire_refresh_lock() {
    if mkdir "$REFRESH_LOCK_DIR" 2> /dev/null; then
        echo "$$" > "$REFRESH_LOCK_DIR/pid"
        return 0
    fi
    lock_holder=$(cat "$REFRESH_LOCK_DIR/pid" 2> /dev/null)
    if [ -n "$lock_holder" ] && kill -0 "$lock_holder" 2> /dev/null; then
        return 1
    fi
    rm -rf "$REFRESH_LOCK_DIR"  # left behind by a run that was killed
    mkdir "$REFRESH_LOCK_DIR" 2> /dev/null && echo "$$" > "$REFRESH_LOCK_DIR/pid"
}

release_refresh_lock() {
    rm -rf "$REFRESH_LOCK_DIR"
}

# Returns 0 = new image, 1 = unchanged, 2 = failed, 3 = another refresh is already running.
refresh_edition() {
    if ! acquire_refresh_lock; then
        log "Aktualisierung läuft bereits"
        return 3
    fi
    if ensure_wifi; then
        download_image
        refresh_result=$?
    else
        log "Kein WLAN – Aktualisierung übersprungen"
        refresh_result=2
    fi
    restore_wifi
    record_refresh_result "$refresh_result"
    release_refresh_lock
    return "$refresh_result"
}
