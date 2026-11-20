#!/bin/sh
# Questions to and requests for the Kindle's power manager (powerd).

# True while the user is using the Kindle (not on the sleep screen, not suspended).
kindle_in_use() {
    case "$(lipc-get-prop com.lab126.powerd state 2> /dev/null)" in
        [Aa]ctive) return 0 ;;
    esac
    return 1
}

set_rtc_wakeup() {
    lipc-set-prop -i com.lab126.powerd rtcWakeup "$1"
}
