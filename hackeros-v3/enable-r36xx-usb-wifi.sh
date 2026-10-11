#!/bin/bash
# R36XX's documented RTL8188ETV radio uses the separate USB host bus.
# Keep the external OTG controller's role, panel and GPIO configuration intact.
set -Eeuo pipefail
ROOT=${1:?Usage: enable-r36xx-usb-wifi.sh MOUNTED_ROOT}
test "$EUID" -eq 0
test -d "$ROOT/boot/dtb/rockchip"
command -v fdtput >/dev/null
command -v fdtget >/dev/null
BACKUP="$ROOT/boot/gamehack-wifi-backup/$(date +%Y%m%d-%H%M%S)"
install -d -o 0 -g 0 -m 0755 "$BACKUP"
for name in rk3326-gameconsole-r36s.dtb rk3326-gameconsole-r36s-host.dtb rk3326-gameconsole-r36s-gadget.dtb; do
    file="$ROOT/boot/dtb/rockchip/$name"
    test -f "$file"
    cp -p "$file" "$BACKUP/$name"
    role=$(fdtget -t s "$file" /usb@ff300000 dr_mode)
    for node in /usb@ff340000 /usb@ff350000; do
        fdtget -t s "$file" "$node" compatible >/dev/null
        fdtput -t s "$file" "$node" status okay
        test "$(fdtget -t s "$file" "$node" status)" = okay
    done
    test "$(fdtget -t s "$file" /usb@ff300000 dr_mode)" = "$role"
    chown 0:0 "$file"
    chmod 0644 "$file"
done
echo "R36XX USB host controllers enabled. Device trees backed up under $BACKUP"
echo 'No GPIO or OTG-role changes. rtl8xxxu must detect the radio on the next boot.'
