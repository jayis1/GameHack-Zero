#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
P=/home/jais/gamehack-companion
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test "$(findmnt -n -o UUID "$R/boot/firmware")" = DA0C-EC97
mount -o remount,rw "$R"
mount -o remount,rw "$R/boot/firmware"
B="$R/opt/gamehack-worker-backup/radio-config-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
cp -p "$R/usr/local/sbin/gamehack-radio" "$R/boot/firmware/cmdline.txt" "$B/"
test ! -e "$R/var/lib/NetworkManager/NetworkManager.state" || cp -p "$R/var/lib/NetworkManager/NetworkManager.state" "$B/"
install -m 0755 "$P/staging/usr/local/sbin/gamehack-radio" "$R/usr/local/sbin/gamehack-radio"
install -D -m 0644 "$P/staging/etc/systemd/journald.conf.d/gamehack.conf" "$R/etc/systemd/journald.conf.d/gamehack.conf"
python3 - "$R" "$B" <<'PY'
from pathlib import Path
import sys, shutil
r, backup = map(Path, sys.argv[1:])
cmdline = r / 'boot/firmware/cmdline.txt'
args = [item for item in cmdline.read_text().split() if not item.startswith('cfg80211.ieee80211_regdom=')]
args.append('cfg80211.ieee80211_regdom=DK')  # Explicitly selected by user.
cmdline.write_text(' '.join(args) + '\n')
state = r / 'var/lib/NetworkManager/NetworkManager.state'
import configparser
config = configparser.ConfigParser()
config.optionxform = str
if state.exists():
    config.read(state)
if not config.has_section('main'):
    config.add_section('main')
config['main']['WirelessEnabled'] = 'true'
state.parent.mkdir(parents=True, exist_ok=True)
with state.open('w') as out:
    config.write(out)
for path in (r / 'var/lib/systemd/rfkill').glob('*:wlan'):
    shutil.copy2(path, backup / path.name)
    path.write_text('0\n')
PY
sync
echo 'Denmark regulatory country, radio-state safeguards and persistent boot logging installed.'
