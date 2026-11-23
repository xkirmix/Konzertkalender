#!/bin/sh
# Loads the Konzertkalender settings and helper modules. Every Kindle-side script sources this file
# (busybox sh on a jailbroken Kindle).
#
# KALENDER_HOME is the folder holding bin/ and konzertkalender.conf. Library scripts use the copy
# installed on the USB storage; the background service runs from a copy in RAM (RUNTIME_HOME) so it
# keeps working while the Kindle is connected to a computer as a USB drive.

#
# The KONZERTKALENDER_* variables only exist so the tests can run these scripts on a computer.

INSTALL_HOME="${KONZERTKALENDER_INSTALL_HOME:-/mnt/us/konzertkalender}"
TMP_DIR="${KONZERTKALENDER_TMP_DIR:-/tmp}"
RUNTIME_HOME="$TMP_DIR/konzertkalender"
KALENDER_HOME="${KALENDER_HOME:-$INSTALL_HOME}"

# Persistent data (image, timestamps, log) lives outside the USB storage for the same reason.
DATA_DIR="${KONZERTKALENDER_DATA_DIR:-/var/local/konzertkalender}"

. "$KALENDER_HOME/konzertkalender.conf"

for kalender_module in log display screen_guard wifi download schedule refresh service browser power events update; do
    . "$KALENDER_HOME/bin/lib_$kalender_module.sh"
done
