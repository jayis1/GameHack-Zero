#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-debug
P=/home/jais/hackeros-v3
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
DTB="$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb"
before="$(sha256sum "$DTB" | awk '{print $1}')"
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/sd2-state-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
for file in usr/local/lib/gamehack-zero/sd2_state.py etc/systemd/system/gamehack-sd2-state.service etc/systemd/system/gamehack-sd2-state.timer; do
    if [ -e "$R/$file" ]; then
        install -d "$B/$(dirname "$file")"
        cp -p "$R/$file" "$B/$file"
    fi
    install -D -m 0644 "$P/staging/$file" "$R/$file"
done
link="$R/etc/systemd/system/timers.target.wants/gamehack-sd2-state.timer"
install -d "$(dirname "$link")"
if [ -e "$link" ] || [ -L "$link" ]; then
    test -L "$link"
    test "$(readlink "$link")" = /etc/systemd/system/gamehack-sd2-state.timer
else
    ln -s /etc/systemd/system/gamehack-sd2-state.timer "$link"
fi
install -m 0644 "$P/DARKOS-SD2-COMPARISON.md" "$R/opt/hackeros/DARKOS-SD2-COMPARISON.md"
test "$before" = "$(sha256sum "$DTB" | awk '{print $1}')"
sync
echo 'One-time SD2 controller diagnostics installed. Active device tree unchanged.'
