#!/bin/sh
# Name: Konzertkalender stoppen
# Author: Konzertkalender
# DontUseFBInk
# Beendet den Kalender-Dienst; der Kindle verhält sich wieder ganz normal.

. "${KONZERTKALENDER_INSTALL_HOME:-/mnt/us/konzertkalender}/bin/kalender_lib.sh"

clear_screen
show_message "Konzertkalender"
if stop_daemon; then
    show_message "Dienst gestoppt. Der Kindle ist wieder normal."
else
    show_message "Der Dienst lief nicht."
fi
