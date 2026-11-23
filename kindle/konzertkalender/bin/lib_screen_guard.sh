#!/bin/sh
# Keeps the calendar on the sleep screen. Amazon redraws its own lock screen (on ad-supported Kindles:
# book ads) whenever the Kindle wakes up briefly. A checksum of the framebuffer, taken right after we
# painted, tells whether anything has drawn over the calendar since.

FRAMEBUFFER="${KONZERTKALENDER_FRAMEBUFFER:-/dev/fb0}"
PAINTED_CHECKSUM_FILE="$TMP_DIR/konzertkalender.painted"
CHECKSUM_BYTES=1048576  # the upper part of the screen is enough to notice a redrawn lock screen

screen_checksum() {
    head -c "$CHECKSUM_BYTES" "$FRAMEBUFFER" 2> /dev/null | cksum
}

paint_calendar() {
    show_image && draw_battery_warning
    screen_checksum > "$PAINTED_CHECKSUM_FILE"
}

# Paints the calendar again if something else has drawn on the screen since we last painted it.
repaint_if_covered() {
    [ -f "$IMAGE_FILE" ] || return 0
    [ "$(screen_checksum)" = "$(cat "$PAINTED_CHECKSUM_FILE" 2> /dev/null)" ] && return 0
    log "Kalender war übermalt – neu gezeichnet"
    paint_calendar
}
