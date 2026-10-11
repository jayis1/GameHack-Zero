#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
P=/home/jais/gamehack-companion
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
mount -o remount,rw "$R"
B="$R/opt/gamehack-worker-backup/usb-managed-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
journalctl --directory="$R/var/log/journal" -b 0 --no-pager > "$B/last-boot.txt"
for file in etc/udev/rules.d/99-gamehack-usb-managed.rules etc/NetworkManager/conf.d/90-gamehack-usb.conf; do
    if [ -e "$R/$file" ]; then
        install -d "$B/$(dirname "$file")"
        cp -p "$R/$file" "$B/$file"
    fi
    install -D -m 0644 "$P/staging/$file" "$R/$file"
done
if [ -f "$R/lib/netplan/00-network-manager-all.yaml" ]; then
    stat -c '%a %n' "$R/lib/netplan/00-network-manager-all.yaml" > "$B/netplan-original-mode.txt"
    chmod 0600 "$R/lib/netplan/00-network-manager-all.yaml"
fi
# Missing ALSA state is normal on a new headless machine. Restore only when
# state exists; do not disable audio or invent a calibration file.
rule="$R/etc/udev/rules.d/90-alsa-restore.rules"
cp -p "$rule" "$B/90-alsa-restore.rules"
python3 - "$rule" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
lines = path.read_text().splitlines()
for index, line in enumerate(lines):
    if 'RUN+=' in line and (' restore ' in line or ' nrestore ' in line) and 'TEST=="/var/lib/alsa/asound.state"' not in line:
        lines[index] = 'TEST=="/var/lib/alsa/asound.state", ' + line
path.write_text('\n'.join(lines) + '\n')
PY
sync
echo 'Paired USB gadget management override and logged warning fixes installed.'
