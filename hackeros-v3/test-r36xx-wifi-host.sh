#!/bin/bash
# Reversible test: allow any radio wired to DWC2 to enumerate as a USB device.
set -Eeuo pipefail
ROOT=/mnt/gamehack-debug
STAGING=/home/jais/hackeros-v3/staging
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$ROOT")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
mount -o remount,rw "$ROOT"
DTB="$ROOT/boot/dtb/rockchip"
BACKUP="$ROOT/boot/gamehack-wifi-backup/host-test-$(date +%Y%m%d-%H%M%S)"
install -d -o 0 -g 0 -m 0755 "$BACKUP"
cp -p "$DTB/rk3326-gameconsole-r36s.dtb" "$BACKUP/"
cp -p "$DTB/rk3326-gameconsole-r36s-host.dtb" "$BACKUP/"
# Derive host mode from the known booting gadget tree, not the base tree,
# whose OTG PHY is disabled.
install -o 0 -g 0 -m 0644 "$DTB/rk3326-gameconsole-r36s-gadget.dtb" "$DTB/rk3326-gameconsole-r36s-host.dtb"
fdtput -t s "$DTB/rk3326-gameconsole-r36s-host.dtb" /usb@ff300000 dr_mode host
test "$(fdtget -t s "$DTB/rk3326-gameconsole-r36s-host.dtb" /syscon@ff2c0000/usb2phy@100/otg-port status)" = okay
test "$(fdtget -t s "$DTB/rk3326-gameconsole-r36s-host.dtb" /usb@ff300000 dr_mode)" = host
install -o 0 -g 0 -m 0644 "$DTB/rk3326-gameconsole-r36s-host.dtb" "$DTB/rk3326-gameconsole-r36s.dtb"
for service in hackeros-gadget.service hackeros-usb-network.service; do
    cp -p "$ROOT/etc/systemd/system/$service" "$BACKUP/"
    install -o 0 -g 0 -m 0644 "$STAGING/etc/systemd/system/$service" "$ROOT/etc/systemd/system/"
done
cp -p "$ROOT/opt/hackeros/launcher.py" "$BACKUP/"
install -o 0 -g 0 -m 0755 "$STAGING/opt/hackeros/launcher.py" "$ROOT/opt/hackeros/launcher.py"
sync
echo "USB-host test prepared. Backups: $BACKUP"
echo 'Boot on battery with the PC OTG cable disconnected. PC-network gadget remains selectable in SYSTEM.'
