#!/bin/sh
# Notices new scripts or settings copied onto the Kindle, so the service can restart itself with them
# (no need to tap "Konzertkalender starten" after an update).

# True when the service runs from its RAM copy and the installed files differ from that copy.
# While the Kindle is a USB drive the installation is not visible; that never counts as a change.
installation_changed() {
    [ "$KALENDER_HOME" = "$RUNTIME_HOME" ] || return 1
    [ -f "$INSTALL_HOME/konzertkalender.conf" ] || return 1
    for installed_file in "$INSTALL_HOME/konzertkalender.conf" "$INSTALL_HOME"/bin/*.sh; do
        relative_path="${installed_file#"$INSTALL_HOME"/}"
        cmp -s "$installed_file" "$RUNTIME_HOME/$relative_path" || return 0
    done
    return 1
}
