#!/bin/bash

set -Eeuo pipefail

TARGET=/dev/sdb
STAGING=/home/jais/hackeros-v3/staging
WORK=/mnt/gamehack-zero-update
ROOT="$WORK/root"
BOOT="$ROOT/boot/u-boot"

die() { echo "ERROR: $*" >&2; exit 1; }

cleanup() {
    sync || true
    mountpoint -q "$BOOT" && umount "$BOOT" || true
    mountpoint -q "$ROOT" && umount "$ROOT" || true
    rmdir "$BOOT" "$ROOT" "$WORK" 2>/dev/null || true
}
trap cleanup EXIT

[ "$EUID" -eq 0 ] || die "Run as root."
[ -b "${TARGET}1" ] && [ -b "${TARGET}2" ] || die "GameHack card not found at $TARGET."
[ "$(blkid -s TYPE -o value "${TARGET}2")" = ext4 ] || die "Unexpected root filesystem."

for part in "${TARGET}1" "${TARGET}2"; do
    while read -r point; do
        [ -n "$point" ] && umount "$point" 2>/dev/null || true
    done < <(findmnt -rn -S "$part" -o TARGET | sort -r)
done

e2label "${TARGET}2" GAMEHACK
mkdir -p "$ROOT"
mount "${TARGET}2" "$ROOT"
mkdir -p "$ROOT/dev" "$ROOT/proc" "$ROOT/run" "$ROOT/sys"
mkdir -p "$BOOT"
mount "${TARGET}1" "$BOOT"
if [ -f "$STAGING/boot-assets/logo.bmp" ]; then
    [ -f "$BOOT/logo-original.bmp" ] || cp "$BOOT/logo.bmp" "$BOOT/logo-original.bmp"
    install -m 0644 "$STAGING/boot-assets/logo.bmp" "$BOOT/logo.bmp"
fi

root_uuid=$(blkid -s UUID -o value "${TARGET}2")
sed -E -i \
    -e "s#root=(LABEL|UUID)=[^ ]+( rootfstype=ext4)?#root=UUID=$root_uuid rootfstype=ext4#" \
    -e 's# rootwait rw( init=/sbin/init)?# rootwait rw init=/sbin/init#' \
    "$BOOT/boot.ini"

rsync -a "$STAGING/etc/" "$ROOT/etc/"
rsync -a "$STAGING/opt/" "$ROOT/opt/"
rsync -a "$STAGING/usr/" "$ROOT/usr/"
/bin/bash /home/jais/hackeros-v3/enable-r36xx-usb-wifi.sh "$ROOT"
install -m 0644 "$STAGING/os-release" "$ROOT/etc/os-release"
install -m 0644 "$STAGING/issue" "$ROOT/etc/issue"
install -m 0440 "$STAGING/hackeros-sudoers" "$ROOT/etc/sudoers.d/hackeros"
chmod 0755 "$ROOT"/usr/local/sbin/hackeros-* "$ROOT/opt/hackeros/launcher.py"
chown 0:0 \
    "$ROOT/etc" "$ROOT/etc/NetworkManager" "$ROOT/etc/NetworkManager/conf.d" \
    "$ROOT/etc/ssh" "$ROOT/etc/ssh/sshd_config.d" \
    "$ROOT/etc/systemd" "$ROOT/etc/systemd/system" \
    "$ROOT/etc/udev" "$ROOT/etc/udev/rules.d" \
    "$ROOT/opt" "$ROOT/usr" "$ROOT/usr/local" "$ROOT/usr/local/lib" "$ROOT/usr/local/sbin"
chown -R 0:0 \
    "$ROOT/etc/hackeros" "$ROOT/etc/systemd/system"/hackeros-*.service \
    "$ROOT/etc/udev/rules.d/70-gamehack-tiqiaa-ir.rules" \
    "$ROOT/etc/udev/rules.d/99-hackeros-storage.rules" \
    "$ROOT/etc/NetworkManager/conf.d/90-hackeros.conf" \
    "$ROOT/etc/ssh/sshd_config.d/90-hackeros.conf" \
    "$ROOT/opt/hackeros" "$ROOT/usr/local/sbin"/hackeros-* \
    "$ROOT/usr/local/lib/gamehack-zero"

hacker_uid=$(awk -F: '$1=="hacker" {print $3}' "$ROOT/etc/passwd")
hacker_gid=$(awk -F: '$1=="hacker" {print $4}' "$ROOT/etc/passwd")
[ -n "$hacker_uid" ] && [ -n "$hacker_gid" ] || die "The hacker account is missing."

mkdir -p "$ROOT/data/gamehack-zero/captures"
if [ -d "$ROOT/data/hackeros" ]; then
    cp -a "$ROOT/data/hackeros/." "$ROOT/data/gamehack-zero/"
fi
chown -R "$hacker_uid:$hacker_gid" "$ROOT/data/gamehack-zero"
if [ -f "$ROOT/etc/hackeros/bootstrap-password" ]; then
    chown "0:$hacker_gid" "$ROOT/etc/hackeros/bootstrap-password"
    chmod 0640 "$ROOT/etc/hackeros/bootstrap-password"
fi
install -o "$hacker_uid" -g "$hacker_gid" -m 0644 \
    "$STAGING/README-FIRST.txt" "$ROOT/home/hacker/README-FIRST.txt"

echo gamehack-zero >"$ROOT/etc/hostname"
if grep -q '^127\.0\.1\.1' "$ROOT/etc/hosts"; then
    sed -i 's/^127\.0\.1\.1.*/127.0.1.1\tgamehack-zero/' "$ROOT/etc/hosts"
else
    printf '127.0.1.1\tgamehack-zero\n' >>"$ROOT/etc/hosts"
fi

systemctl --root="$ROOT" enable bluetooth.service NetworkManager.service \
    hackeros-gadget.service hackeros-usb-network.service \
    hackeros-storage.service hackeros-ui.service ssh.service
systemctl --root="$ROOT" disable serial-getty@ttyS0.service || true
systemctl --root="$ROOT" mask serial-getty@ttyS0.service

sync
echo "Installed card updated to GameHack Zero V3."
