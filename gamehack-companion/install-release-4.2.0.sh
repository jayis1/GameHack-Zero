#!/bin/bash
# Version the existing, tested companion without changing its network or keys.
set -Eeuo pipefail
R=${1:-/mnt/gamehack-pi}
P=$(cd -- "$(dirname -- "$0")" && pwd)
test "$EUID" -eq 0
test "$(findmnt -n -o UUID --mountpoint "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test -f "$R/etc/systemd/system/gamehack-usb-ncm.service"
mount -o remount,rw "$R"
B="$R/opt/gamehack-worker-backup/release-4.2.0-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
for file in usr/local/bin/gamehack-companion etc/gamehack-companion-release; do
    if [ -e "$R/$file" ]; then
        install -d "$B/$(dirname "$file")"
        cp -p "$R/$file" "$B/$file"
    fi
    mode=0644
    case "$file" in usr/local/bin/*) mode=0755 ;; esac
    install -D -o 0 -g 0 -m "$mode" "$P/staging/$file" "$R/$file"
    cmp "$P/staging/$file" "$R/$file"
done
sync
echo 'Pi companion release 4.2.0 installed; worker protocol remains 2.'
echo 'Existing NCM, DK radio configuration, keys, tasks and Pi OS identity untouched.'
