#!/bin/bash
set -Eeuo pipefail
ROOT=${1:-/mnt/gamehack-debug}
PROJECT=/home/jais/hackeros-v3
STAGING="$PROJECT/staging"
KERNEL=6.12.32-lts-rk3326
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$ROOT")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
test -d "$ROOT/lib/modules/$KERNEL"
test "$(fdtget -t s "$ROOT/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb" /usb@ff300000 dr_mode)" = host
mount -o remount,rw "$ROOT"
BACKUP="$ROOT/opt/hackeros/update-backup/$(date +%Y%m%d-%H%M%S)"
install -d -o 0 -g 0 -m 0755 "$BACKUP"
cp -p "$ROOT/opt/hackeros/launcher.py" "$ROOT/opt/hackeros/freedoom_runner.py" "$BACKUP/"
cp -p "$ROOT/usr/local/sbin/hackeros-action" "$BACKUP/"
install -o 0 -g 0 -m 0755 "$STAGING/opt/hackeros/launcher.py" "$ROOT/opt/hackeros/launcher.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/freedoom_runner.py" "$ROOT/opt/hackeros/freedoom_runner.py"
install -o 0 -g 0 -m 0755 "$STAGING/usr/local/sbin/hackeros-action" "$ROOT/usr/local/sbin/hackeros-action"
install -d -o 0 -g 0 -m 0755 "$ROOT/usr/local/lib/gamehack-zero"
install -o 0 -g 0 -m 0644 "$STAGING/usr/local/lib/gamehack-zero/monitor_wifi.py" "$ROOT/usr/local/lib/gamehack-zero/monitor_wifi.py"
install -o 1000 -g 1000 -m 0644 "$STAGING/README-FIRST.txt" "$ROOT/home/hacker/README-FIRST.txt"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/MOMENTUM-INSPIRED.md" "$ROOT/opt/hackeros/MOMENTUM-INSPIRED.md"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/EXTERNAL-WIFI.md" "$ROOT/opt/hackeros/EXTERNAL-WIFI.md"
install -d -o 0 -g 0 -m 0755 "$ROOT/lib/modules/$KERNEL/extra/gamehack"
for module in rtw88_usb rtw88_8821c rtw88_8821cu; do
    file="$PROJECT/driver-build/$KERNEL/$module.ko"
    test "$(modinfo -F vermagic "$file")" = "$(modinfo -F vermagic "$ROOT/lib/modules/$KERNEL/kernel/drivers/net/wireless/realtek/rtw88/rtw88_core.ko")"
    test ! -e "$ROOT/lib/modules/$KERNEL/extra/gamehack/$module.ko" || cp -p "$ROOT/lib/modules/$KERNEL/extra/gamehack/$module.ko" "$BACKUP/"
    install -o 0 -g 0 -m 0644 "$file" "$ROOT/lib/modules/$KERNEL/extra/gamehack/"
done
depmod -b "$ROOT" "$KERNEL"
test -s "$ROOT/lib/firmware/rtw88/rtw8821c_fw.bin"
grep -q 'v0BDApC820.*rtw88_8821cu' "$ROOT/lib/modules/$KERNEL/modules.alias"
sync
echo 'External adapter driver and monitor workflow installed; real hardware test required.'
