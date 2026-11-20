#!/bin/sh
# Downloads the calendar image, checks that it really is a PNG and keeps the previous image when
# anything goes wrong.

DOWNLOAD_TIMEOUT_SECONDS=90

file_is_png() {
    [ "$(dd if="$1" bs=1 skip=1 count=3 2> /dev/null)" = "PNG" ]
}

# Returns 0 = new image stored, 1 = unchanged, 2 = failed.
download_image() {
    mkdir -p "$DATA_DIR"
    partial_file="$DATA_DIR/download.part"
    rm -f "$partial_file"
    if ! curl -fsSL --max-time "$DOWNLOAD_TIMEOUT_SECONDS" -o "$partial_file" "$IMAGE_URL"; then
        log "Download fehlgeschlagen: $IMAGE_URL"
        rm -f "$partial_file"
        return 2
    fi
    if ! file_is_png "$partial_file"; then
        log "Antwort ist kein PNG – Adresse in konzertkalender.conf prüfen"
        rm -f "$partial_file"
        return 2
    fi
    if [ -f "$IMAGE_FILE" ] && cmp -s "$partial_file" "$IMAGE_FILE"; then
        rm -f "$partial_file"
        return 1
    fi
    mv -f "$partial_file" "$IMAGE_FILE"
    log "Neue Ausgabe geladen"
    return 0
}
