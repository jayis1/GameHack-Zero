#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0
R=/mnt/gamehack-debug
P=/home/jais/hackeros-v3
S="$P/staging"
ACCESS=/home/jais/gamehack-companion/access
test "$(findmnt -n -o UUID "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
test "$(fdtget -t s "$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb" /usb@ff300000 dr_mode)" = host
test -s "$ACCESS/gamehack-pi-ed25519"
test -s "$ACCESS/known_hosts"
mount -o remount,rw "$R"
BACKUP="$R/opt/hackeros/update-backup/pi-worker-$(date +%Y%m%d-%H%M%S)"
install -d -m 0755 "$BACKUP"
for relative in opt/hackeros/launcher.py etc/NetworkManager/conf.d/90-hackeros.conf etc/systemd/system/hackeros-usb-network.service; do
    install -D -m 0644 "$R/$relative" "$BACKUP/$relative"
done
for relative in opt/hackeros/launcher.py opt/hackeros/pi_worker.py opt/hackeros/PI-WORKER.md etc/NetworkManager/conf.d/90-hackeros.conf etc/systemd/system/hackeros-usb-network.service; do
    install -D -o 0 -g 0 -m 0644 "$S/$relative" "$R/$relative"
done
chmod 0755 "$R/opt/hackeros/launcher.py"
PROFILE=etc/NetworkManager/system-connections/gamehack-pi-worker.nmconnection
test ! -e "$R/$PROFILE" || install -D -m 0600 "$R/$PROFILE" "$BACKUP/$PROFILE"
install -D -o 0 -g 0 -m 0600 "$S/$PROFILE" "$R/$PROFILE"
test ! -e "$R/home/hacker/.ssh/gamehack-pi"
install -d -o 1000 -g 1000 -m 0700 "$R/home/hacker/.ssh" "$R/home/hacker/.ssh/gamehack-pi"
install -o 1000 -g 1000 -m 0600 "$ACCESS/gamehack-pi-ed25519" "$R/home/hacker/.ssh/gamehack-pi/id_ed25519"
install -o 1000 -g 1000 -m 0600 "$ACCESS/known_hosts" "$R/home/hacker/.ssh/gamehack-pi/known_hosts"
sync
echo 'Pi worker controls and dedicated non-default USB profile installed. USB hardware issue remains to be tested.'
