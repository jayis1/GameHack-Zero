#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0
R=/mnt/gamehack-debug
P=/home/jais/hackeros-v3
test "$(findmnt -n -o UUID "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
test "$(fdtget -t s "$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb" /usb@ff300000 dr_mode)" = host
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/log-repair-$(date +%Y%m%d-%H%M%S)"
install -d -m 0755 "$B"
cp -p "$R/opt/hackeros/launcher.py" "$B/"
install -o 0 -g 0 -m 0755 "$P/staging/opt/hackeros/launcher.py" "$R/opt/hackeros/launcher.py"
# Retain every vendor controller rule, but restore calibration only if saved.
sed 's|^RUN+="/usr/bin/jscal-restore %E{DEVNAME}"|TEST=="/var/lib/joystick/joystick.state", RUN+="/usr/bin/jscal-restore %E{DEVNAME}"|' "$R/usr/lib/udev/rules.d/60-joystick.rules" > "$B/60-joystick.rules"
test ! -e "$R/etc/udev/rules.d/60-joystick.rules" || cmp "$B/60-joystick.rules" "$R/etc/udev/rules.d/60-joystick.rules"
install -m 0644 "$B/60-joystick.rules" "$R/etc/udev/rules.d/60-joystick.rules"
chmod 0644 "$R/etc/udev/rules.d/60-joystick.rules"
# Armbian RAM logging makes the journal a mount point. The optional no-COW
# attribute rule is irrelevant here and produces an error for that mount.
if test -e "$R/etc/tmpfiles.d/journal-nocow.conf" || test -L "$R/etc/tmpfiles.d/journal-nocow.conf"; then
    test "$(readlink "$R/etc/tmpfiles.d/journal-nocow.conf")" = /dev/null
else
    ln -s /dev/null "$R/etc/tmpfiles.d/journal-nocow.conf"
fi
test ! -e "$R/usr/bin/qemu-aarch64-static"
REMOVE_POLICY=no
if test -e "$R/usr/sbin/policy-rc.d"; then
    printf '#!/bin/sh\nexit 101\n' | cmp - "$R/usr/sbin/policy-rc.d"
else
    printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"
    chmod 0755 "$R/usr/sbin/policy-rc.d"
    REMOVE_POLICY=yes
fi
install -m 0755 /usr/bin/qemu-aarch64-static "$R/usr/bin/qemu-aarch64-static"
test ! -e "$R/etc/resolv.conf.logged-repair" && test ! -L "$R/etc/resolv.conf.logged-repair"
mv "$R/etc/resolv.conf" "$R/etc/resolv.conf.logged-repair"
cp -L /etc/resolv.conf "$R/etc/resolv.conf"
mount --bind /dev "$R/dev"
mount --bind /dev/pts "$R/dev/pts"
mount -t proc proc "$R/proc"
trap 'umount "$R/proc"; umount "$R/dev/pts"; umount "$R/dev"; rm -f "$R/usr/bin/qemu-aarch64-static" "$R/etc/resolv.conf"; mv "$R/etc/resolv.conf.logged-repair" "$R/etc/resolv.conf"; if test "$REMOVE_POLICY" = yes; then rm -f "$R/usr/sbin/policy-rc.d"; fi' EXIT
ulimit -c 0
export LC_ALL=C
arm() { chroot "$R" /usr/bin/qemu-aarch64-static "$@"; }
APT=(-o Dir::Etc::sourcelist=sources.list.d/debian.sources -o Dir::Etc::sourceparts=-)
arm /usr/bin/apt-get "${APT[@]}" update
arm /usr/bin/apt-get "${APT[@]}" install -y --no-install-recommends libblockdev-crypto2 libblockdev-mdraid2 libnss-mdns
arm /usr/bin/apt-get clean
sync
echo 'Logged software error fixes installed; hardware USB fault and sound still require device testing.'
