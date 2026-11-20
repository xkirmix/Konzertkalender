#!/bin/sh
# Logging: one timestamped line per call. The main log sits next to the data; a copy goes to the
# USB storage (when it is mounted) so the log can be read from a computer.

LOG_FILE="$DATA_DIR/konzertkalender.log"
USB_LOG_FILE="$INSTALL_HOME/konzertkalender.log"
LOG_MAX_BYTES=200000

rotate_if_large() {
    [ -f "$1" ] || return 0
    if [ "$(wc -c < "$1")" -gt "$LOG_MAX_BYTES" ]; then
        mv -f "$1" "$1.old"
    fi
    return 0
}

log() {
    line="$(date '+%Y-%m-%d %H:%M:%S') $*"
    mkdir -p "$DATA_DIR"
    rotate_if_large "$LOG_FILE"
    echo "$line" >> "$LOG_FILE"
    if [ -d "$INSTALL_HOME" ]; then
        rotate_if_large "$USB_LOG_FILE"
        echo "$line" >> "$USB_LOG_FILE" 2> /dev/null
    fi
    return 0
}
