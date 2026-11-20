#!/bin/sh
# Opens the clickable calendar page in the Kindle's built-in browser.

open_page() {
    if ! lipc-set-prop com.lab126.appmgrd start "app://com.lab126.browser?view=$PAGE_URL" 2>> "$LOG_FILE"; then
        log "Browser konnte nicht geöffnet werden"
        return 1
    fi
    log "Seite geöffnet: $PAGE_URL"
}
