#!/bin/sh
# When to fetch the next edition: REFRESH_HOURS after the last successful refresh, or RETRY_MINUTES
# after a failed attempt.

LAST_SUCCESS_FILE="$DATA_DIR/last_success"
LAST_ATTEMPT_FILE="$DATA_DIR/last_attempt"
LAST_RESULT_FILE="$DATA_DIR/last_result"
MINIMUM_WAKEUP_SECONDS=120
DUE_TOLERANCE_SECONDS=300

now_epoch() {
    date +%s
}

read_epoch() {
    cat "$1" 2> /dev/null || echo 0
}

# Stores the outcome of a refresh; $1 is the download_image result (0 new, 1 unchanged, 2 failed).
record_refresh_result() {
    mkdir -p "$DATA_DIR"
    attempt_epoch=$(now_epoch)
    echo "$attempt_epoch" > "$LAST_ATTEMPT_FILE"
    if [ "$1" -le 1 ]; then
        echo "$attempt_epoch" > "$LAST_SUCCESS_FILE"
    fi
    echo "$1" > "$LAST_RESULT_FILE"
}

last_refresh_failed() {
    [ "$(read_epoch "$LAST_ATTEMPT_FILE")" -gt "$(read_epoch "$LAST_SUCCESS_FILE")" ]
}

next_refresh_epoch() {
    # A timestamp in the future means the clock was set back: refresh right away.
    if [ "$(read_epoch "$LAST_ATTEMPT_FILE")" -gt "$(now_epoch)" ]; then
        echo 0
    elif last_refresh_failed; then
        echo $(( $(read_epoch "$LAST_ATTEMPT_FILE") + RETRY_MINUTES * 60 ))
    else
        echo $(( $(read_epoch "$LAST_SUCCESS_FILE") + REFRESH_HOURS * 3600 ))
    fi
}

refresh_is_due() {
    [ "$(now_epoch)" -ge $(( $(next_refresh_epoch) - DUE_TOLERANCE_SECONDS )) ]
}

seconds_until_refresh() {
    remaining_seconds=$(( $(next_refresh_epoch) - $(now_epoch) ))
    if [ "$remaining_seconds" -lt "$MINIMUM_WAKEUP_SECONDS" ]; then
        remaining_seconds=$MINIMUM_WAKEUP_SECONDS
    fi
    echo "$remaining_seconds"
}
