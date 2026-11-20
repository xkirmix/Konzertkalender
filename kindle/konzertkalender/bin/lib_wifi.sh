#!/bin/sh
# WiFi handling: switches WiFi on for a download and back off afterwards if it was off before.

WIFI_TIMEOUT_SECONDS=60
WIFI_SETTLE_SECONDS=3
WIFI_SWITCHED_ON_BY_US=0

wifi_is_connected() {
    [ "$(lipc-get-prop com.lab126.wifid cmState 2> /dev/null)" = "CONNECTED" ]
}

# Switches WiFi on if needed and waits for a connection. Remembers whether we switched it on.
ensure_wifi() {
    WIFI_SWITCHED_ON_BY_US=0
    wifi_is_connected && return 0
    WIFI_SWITCHED_ON_BY_US=1
    lipc-set-prop com.lab126.cmd wirelessEnable 1
    wifi_waited=0
    while [ "$wifi_waited" -lt "$WIFI_TIMEOUT_SECONDS" ]; do
        if wifi_is_connected; then
            sleep "$WIFI_SETTLE_SECONDS"  # give DHCP and DNS a moment
            return 0
        fi
        sleep 2
        wifi_waited=$((wifi_waited + 2))
    done
    return 1
}

restore_wifi() {
    if [ "$WIFI_SWITCHED_ON_BY_US" = "1" ]; then
        lipc-set-prop com.lab126.cmd wirelessEnable 0
    fi
    WIFI_SWITCHED_ON_BY_US=0
}
