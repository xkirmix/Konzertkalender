#!/bin/sh
# Name: Konzertkalender Diagnose
# Author: Konzertkalender
# DontUseFBInk
# Sammelt Infos für die Fehlersuche in konzertkalender/diagnose.txt (verändert nichts).

. "${KONZERTKALENDER_INSTALL_HOME:-/mnt/us/konzertkalender}/bin/kalender_lib.sh"

clear_screen
show_message "Konzertkalender Diagnose"
show_message "Sammle Infos (ca. 1 Minute) ..."
start_detached /bin/sh "$INSTALL_HOME/bin/kalender_diagnose.sh"
