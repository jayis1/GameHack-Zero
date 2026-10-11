#!/bin/bash
set -Eeuo pipefail
ROOT=/mnt/gamehack-debug
STAGING=/home/jais/hackeros-v3/staging
test "$EUID" -eq 0
test "$(findmnt -n -o SOURCE "$ROOT")" = /dev/sda2
test "$(blkid -s UUID -o value /dev/sda2)" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
mount -o remount,rw "$ROOT"

cleanup() {
    umount "$ROOT/dev/pts" 2>/dev/null || true
    umount "$ROOT/proc" 2>/dev/null || true
    umount "$ROOT/dev" 2>/dev/null || true
    if test -e "$ROOT/etc/resolv.conf.gamehack-repair" || test -L "$ROOT/etc/resolv.conf.gamehack-repair"; then
        rm -f "$ROOT/etc/resolv.conf"
        mv "$ROOT/etc/resolv.conf.gamehack-repair" "$ROOT/etc/resolv.conf"
    fi
    rm -f "$ROOT/usr/bin/qemu-aarch64-static"
    sync
}
trap cleanup EXIT

install -d -m 0755 "$ROOT/etc/systemd/system/ssh.service.d"
install -m 0644 "$STAGING/etc/systemd/system/ssh.service.d/10-gamehack-hostkeys.conf" "$ROOT/etc/systemd/system/ssh.service.d/"
install -m 0644 "$STAGING/etc/systemd/system/hackeros-ui.service" "$ROOT/etc/systemd/system/"
systemctl --root="$ROOT" disable serial-getty@ttyS0.service
systemctl --root="$ROOT" mask serial-getty@ttyS0.service

cp /usr/bin/qemu-aarch64-static "$ROOT/usr/bin/"
if ! test -e "$ROOT/etc/resolv.conf.gamehack-repair" && ! test -L "$ROOT/etc/resolv.conf.gamehack-repair"; then
    mv "$ROOT/etc/resolv.conf" "$ROOT/etc/resolv.conf.gamehack-repair"
else
    rm -f "$ROOT/etc/resolv.conf"
fi
cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
mount --bind /dev "$ROOT/dev"
mount --bind /dev/pts "$ROOT/dev/pts"
mount -t proc proc "$ROOT/proc"
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/apt-get \
    -o Dir::Etc::sourcelist=sources.list.d/debian.sources \
    -o Dir::Etc::sourceparts=- update
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/apt-get -y \
    -o Dir::Etc::sourcelist=sources.list.d/debian.sources \
    -o Dir::Etc::sourceparts=- --reinstall install \
    libgl1-mesa-dri libegl-mesa0 libgbm1 libdrm-amdgpu1 libdrm-nouveau2 \
    libdrm-radeon1 libglapi-mesa libxcb-dri2-0 libxcb-present0 libxcb-randr0 \
    libxcb-sync1 libxcb-xfixes0 libxshmfence1 libc6 libc-bin libegl1 libgles2 libgl1
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/ssh-keygen -A
mkdir -p "$ROOT/run/sshd"
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/sbin/sshd -t
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/dpkg --verify \
    libgl1-mesa-dri libegl-mesa0 libgbm1 libdrm-amdgpu1 libdrm-nouveau2 \
    libdrm-radeon1 libglapi-mesa libxcb-dri2-0 libxcb-present0 libxcb-randr0 \
    libxcb-sync1 libxcb-xfixes0 libxshmfence1 libc6 libc-bin libegl1 libgles2 libgl1
chroot "$ROOT" /usr/bin/qemu-aarch64-static /usr/bin/python3 -c \
    'import ctypes; [ctypes.CDLL(name) for name in ("libEGL.so.1", "libGLESv2.so.2", "libGL.so.1")]; print("EGL, GLES and GL runtime libraries load successfully")'
echo 'SSH configuration validated; serial console disabled; Mesa drivers installed.'
