#!/bin/sh
# Drawing on the e-ink screen: the calendar image, short status lines and the battery hint.
# Uses FBInk from the jailbreak when available and falls back to the stock eips tool.

IMAGE_FILE="$DATA_DIR/kalender.png"
START_IMAGE_FILE="$INSTALL_HOME/startbild.png"
FBINK_CANDIDATES="/var/local/kmc/bin/fbink /mnt/us/libkh/bin/fbink /usr/bin/fbink"
MESSAGE_ROW=4

find_fbink() {
    for fbink_candidate in $FBINK_CANDIDATES; do
        if [ -x "$fbink_candidate" ]; then
            echo "$fbink_candidate"
            return 0
        fi
    done
    return 1
}

FBINK="$(find_fbink)"

# Until the first download succeeds, the picture shipped with the installation is shown.
use_start_image_if_missing() {
    if [ ! -f "$IMAGE_FILE" ] && [ -f "$START_IMAGE_FILE" ]; then
        mkdir -p "$DATA_DIR"
        cp -f "$START_IMAGE_FILE" "$IMAGE_FILE"
        log "Startbild übernommen"
    fi
}

show_image() {
    [ -f "$IMAGE_FILE" ] || return 1
    if [ -n "$FBINK" ]; then
        "$FBINK" -q -c -f -g file="$IMAGE_FILE"
    else
        eips -f -g "$IMAGE_FILE"
    fi
}

clear_screen() {
    MESSAGE_ROW=4
    if [ -n "$FBINK" ]; then
        "$FBINK" -q -c -f
    else
        eips -c
    fi
}

# Writes one status line below the previous one (feedback for the library scripts).
show_message() {
    if [ -n "$FBINK" ]; then
        "$FBINK" -q -y "$MESSAGE_ROW" "$*"
    else
        eips 1 "$MESSAGE_ROW" "$*"
    fi
    MESSAGE_ROW=$((MESSAGE_ROW + 2))
}

draw_battery_warning() {
    battery_level=$(lipc-get-prop com.lab126.powerd battLevel 2> /dev/null)
    [ -n "$battery_level" ] && [ -n "$FBINK" ] || return 0
    if [ "$battery_level" -lt "$LOW_BATTERY_PERCENT" ]; then
        "$FBINK" -q -m -y -3 "Akku ${battery_level}% - bitte laden"
    fi
    return 0
}
