#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0 || { echo 'Run as root.' >&2; exit 1; }
STAGING=/home/jais/hackeros-v3/staging
ROOT_PART=$(blkid -U 2ac15f87-aa0e-4fa6-9437-b542636d070c)
BOOT_PART=$(blkid -U 1A45-2972)
test -b "$ROOT_PART" && test -b "$BOOT_PART"
test "$(lsblk -no PKNAME "$ROOT_PART")" = "$(lsblk -no PKNAME "$BOOT_PART")"
WORK=/mnt/gamehack-customization
ROOT="$WORK/root"
BOOT="$WORK/boot"
mkdir -p "$ROOT" "$BOOT"
cleanup() {
    sync
    mountpoint -q "$BOOT" && umount "$BOOT" || true
    mountpoint -q "$ROOT" && umount "$ROOT" || true
}
trap cleanup EXIT
for part in "$ROOT_PART" "$BOOT_PART"; do
    if findmnt -rn -S "$part" >/dev/null; then
        echo "Unmount $part before deploying." >&2
        exit 1
    fi
done
mount "$ROOT_PART" "$ROOT"
mount "$BOOT_PART" "$BOOT"
test -f "$ROOT/opt/hackeros/launcher.py"
test -f "$ROOT/usr/lib/aarch64-linux-gnu/dri/rockchip_dri.so"
# Update UI, scoped network authorization, help, and early boot image.
install -o 0 -g 0 -m 0755 "$STAGING/opt/hackeros/launcher.py" "$ROOT/opt/hackeros/launcher.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/customization.py" "$ROOT/opt/hackeros/customization.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/wifi_tools.py" "$ROOT/opt/hackeros/wifi_tools.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/prompt_job.py" "$ROOT/opt/hackeros/prompt_job.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/freedoom_runner.py" "$ROOT/opt/hackeros/freedoom_runner.py"
install -o 0 -g 0 -m 0755 "$STAGING/usr/local/bin/opencode" "$ROOT/usr/local/bin/opencode"
install -o 0 -g 0 -m 0755 "$STAGING/usr/local/sbin/hackeros-action" "$ROOT/usr/local/sbin/hackeros-action"
install -d -o 0 -g 0 -m 0755 "$ROOT/etc/polkit-1/rules.d"
install -o 0 -g 0 -m 0644 "$STAGING/etc/polkit-1/rules.d/49-gamehack-network.rules" "$ROOT/etc/polkit-1/rules.d/49-gamehack-network.rules"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/MOMENTUM-INSPIRED.md" "$ROOT/opt/hackeros/MOMENTUM-INSPIRED.md"
install -o 1000 -g 1000 -m 0644 "$STAGING/README-FIRST.txt" "$ROOT/home/hacker/README-FIRST.txt"
test -f "$BOOT/logo-original.bmp" || cp "$BOOT/logo.bmp" "$BOOT/logo-original.bmp"
install -m 0644 "$STAGING/boot-assets/logo.bmp" "$BOOT/logo.bmp"
echo 'Customization and GameHack Zero boot splash deployed; original logo preserved.'
