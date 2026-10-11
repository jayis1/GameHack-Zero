#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-debug
P=/home/jais/hackeros-v3
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
test -f "$R/lib/modules/6.12.32-lts-rk3326/kernel/fs/exfat/exfat.ko"
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/sd2-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
files=(usr/local/sbin/hackeros-storage usr/local/sbin/hackeros-report usr/local/sbin/hackeros-action
       usr/local/lib/gamehack-zero/sd2_debug.py opt/hackeros/launcher.py opt/hackeros/freedoom_runner.py
       etc/systemd/system/gamehack-sd2-debug.service etc/systemd/system/gamehack-sd2-debug.timer
       etc/systemd/journald.conf.d/gamehack-debug.conf)
for file in "${files[@]}"; do
    if [ -f "$R/$file" ]; then
        install -d "$B/$(dirname "$file")"
        cp -p "$R/$file" "$B/$file"
    fi
    mode=0644
    case "$file" in usr/local/sbin/*|opt/hackeros/launcher.py|opt/hackeros/freedoom_runner.py) mode=0755;; esac
    install -D -m "$mode" "$P/staging/$file" "$R/$file"
done
# Armbian RAM logging otherwise hides recent journals on unexpected shutdown.
# Disable only the RAM-log mount; retain zram swap and all existing logs.
cp -p "$R/etc/default/armbian-ramlog" "$B/armbian-ramlog"
sed -i 's/^ENABLED=true$/ENABLED=false/' "$R/etc/default/armbian-ramlog"
install -d -m 0755 "$R/etc/systemd/system/timers.target.wants"
ln -sfn /etc/systemd/system/gamehack-sd2-debug.timer "$R/etc/systemd/system/timers.target.wants/gamehack-sd2-debug.timer"
install -d -o 0 -g 0 -m 0755 "$R/data/debug"
install -m 0644 "$P/SD2-STORAGE.md" "$R/opt/hackeros/SD2-STORAGE.md"
sync
echo 'SD2 mount, bounded diagnostics, safe eject and Freedoom integration installed.'
