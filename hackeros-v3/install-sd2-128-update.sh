#!/bin/bash
# Accept both specifically prepared SD2 cards; do not mount arbitrary media.
set -Eeuo pipefail
R=${1:-/mnt/gamehack-debug}
P=$(cd -- "$(dirname -- "$0")" && pwd)
test "$EUID" -eq 0
test "$(findmnt -n -o UUID --mountpoint "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
grep -qx 'VERSION="4.2.0"' "$R/etc/hackeros/release"
before=$(sha256sum "$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb" | awk '{print $1}')
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/sd2-128-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
for file in usr/local/sbin/hackeros-storage usr/local/lib/gamehack-zero/sd2_debug.py; do
    test -f "$R/$file"
    install -d "$B/$(dirname "$file")"
    cp -p "$R/$file" "$B/$file"
    mode=0644
    case "$file" in usr/local/sbin/*) mode=0755 ;; esac
    install -o 0 -g 0 -m "$mode" "$P/staging/$file" "$R/$file"
    cmp "$P/staging/$file" "$R/$file"
done
if [ -f "$R/opt/hackeros/SD2-STORAGE.md" ]; then
    cp -p "$R/opt/hackeros/SD2-STORAGE.md" "$B/SD2-STORAGE.md"
fi
install -m 0644 "$P/SD2-STORAGE.md" "$R/opt/hackeros/SD2-STORAGE.md"
test "$before" = "$(sha256sum "$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb" | awk '{print $1}')"
sync
echo '128GB SD2 UUIDs accepted; original 256GB UUIDs retained. Kernel/DTB unchanged.'
