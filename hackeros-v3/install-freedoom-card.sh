#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0
STAGING=/home/jais/hackeros-v3/staging
PART=$(blkid -U 2ac15f87-aa0e-4fa6-9437-b542636d070c)
ROOT=/mnt/gamehack-freedoom
test -b "$PART"
if findmnt -rn -S "$PART" >/dev/null; then
    echo 'Unmount the GameHack root partition first.' >&2
    exit 1
fi
mkdir -p "$ROOT"
mount "$PART" "$ROOT"
QEMU_ADDED=0
RESOLV_SAVED=0
cleanup() {
    umount "$ROOT/proc" 2>/dev/null || true
    umount "$ROOT/dev/pts" 2>/dev/null || true
    umount "$ROOT/dev" 2>/dev/null || true
    if test "$RESOLV_SAVED" -eq 1; then
        rm -f "$ROOT/etc/resolv.conf"
        mv "$ROOT/etc/resolv.conf.gamehack-freedoom" "$ROOT/etc/resolv.conf"
    fi
    if test "$QEMU_ADDED" -eq 1; then
        rm -f "$ROOT/usr/bin/qemu-aarch64-static"
    fi
    sync
    umount "$ROOT"
}
trap cleanup EXIT
test -f "$ROOT/opt/hackeros/launcher.py"
test -f "$STAGING/opt/freedoom/freedoom1.wad"
test ! -e "$ROOT/usr/bin/qemu-aarch64-static"
test ! -L "$ROOT/usr/bin/qemu-aarch64-static"
test ! -e "$ROOT/etc/resolv.conf.gamehack-freedoom"
test ! -L "$ROOT/etc/resolv.conf.gamehack-freedoom"
cp /usr/bin/qemu-aarch64-static "$ROOT/usr/bin/"
QEMU_ADDED=1
mv "$ROOT/etc/resolv.conf" "$ROOT/etc/resolv.conf.gamehack-freedoom"
RESOLV_SAVED=1
cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
mount --bind /dev "$ROOT/dev"
mount --bind /dev/pts "$ROOT/dev/pts"
mount -t proc proc "$ROOT/proc"
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/apt-get \
    -o Dir::Etc::sourcelist=sources.list.d/debian.sources -o Dir::Etc::sourceparts=- update
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/apt-get -y --no-install-recommends \
    -o Dir::Etc::sourcelist=sources.list.d/debian.sources -o Dir::Etc::sourceparts=- install crispy-doom
install -d -o 0 -g 0 -m 0755 "$ROOT/opt/freedoom"
for file in freedoom1.wad freedoom2.wad COPYING.txt README.html CREDITS.txt CREDITS-MUSIC.txt; do
    install -o 0 -g 0 -m 0644 "$STAGING/opt/freedoom/$file" "$ROOT/opt/freedoom/"
    cmp "$STAGING/opt/freedoom/$file" "$ROOT/opt/freedoom/$file"
done
install -o 0 -g 0 -m 0755 "$STAGING/opt/hackeros/launcher.py" "$ROOT/opt/hackeros/launcher.py"
install -o 0 -g 0 -m 0644 "$STAGING/opt/hackeros/freedoom_runner.py" "$ROOT/opt/hackeros/freedoom_runner.py"
install -o 0 -g 0 -m 0644 "$STAGING/etc/udev/rules.d/71-gamehack-uinput.rules" "$ROOT/etc/udev/rules.d/"
install -o 0 -g 0 -m 0644 "$STAGING/etc/modules-load.d/gamehack-games.conf" "$ROOT/etc/modules-load.d/"
install -o 1000 -g 1000 -m 0644 "$STAGING/README-FIRST.txt" "$ROOT/home/hacker/README-FIRST.txt"
test -f "$ROOT/usr/games/crispy-doom"
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/dpkg --verify crispy-doom
echo 'Freedoom Phase 1+2 installed. Wi-Fi device trees unchanged. Hardware gameplay test required.'
