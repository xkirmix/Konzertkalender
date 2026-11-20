#!/bin/sh
# Fetches the newest edition once (started by "Konzertkalender starten").

KALENDER_HOME="$(cd "$(dirname "$0")/.." && pwd)"
. "$KALENDER_HOME/bin/kalender_lib.sh"

refresh_edition
