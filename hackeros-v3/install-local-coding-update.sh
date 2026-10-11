#!/bin/bash
set -Eeuo pipefail
R=${1:-/mnt/gamehack-debug}
P=/home/jais/hackeros-v3
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/local-coding-$(date +%Y%m%d-%H%M%S)"
install -d -m 0755 "$B"
cp -p "$R/opt/hackeros/launcher.py" "$B/"
test ! -e "$R/usr/bin/qemu-aarch64-static"
test ! -e "$R/etc/resolv.conf.local-coding" && test ! -L "$R/etc/resolv.conf.local-coding"
REMOVE_POLICY=no
if test -e "$R/usr/sbin/policy-rc.d"; then
    printf '#!/bin/sh\nexit 101\n' | cmp - "$R/usr/sbin/policy-rc.d"
else
    printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"
    chmod 0755 "$R/usr/sbin/policy-rc.d"
    REMOVE_POLICY=yes
fi
install -m 0755 /usr/bin/qemu-aarch64-static "$R/usr/bin/qemu-aarch64-static"
mv "$R/etc/resolv.conf" "$R/etc/resolv.conf.local-coding"
cp -L /etc/resolv.conf "$R/etc/resolv.conf"
mount --bind /dev "$R/dev"
mount --bind /dev/pts "$R/dev/pts"
mount -t proc proc "$R/proc"
trap 'umount "$R/proc"; umount "$R/dev/pts"; umount "$R/dev"; rm -f "$R/usr/bin/qemu-aarch64-static" "$R/etc/resolv.conf"; mv "$R/etc/resolv.conf.local-coding" "$R/etc/resolv.conf"; if test "$REMOVE_POLICY" = yes; then rm -f "$R/usr/sbin/policy-rc.d"; fi' EXIT
ulimit -c 0
export LC_ALL=C
arm() { chroot "$R" /usr/bin/qemu-aarch64-static "$@"; }
APT=(-o Dir::Etc::sourcelist=sources.list.d/debian.sources -o Dir::Etc::sourceparts=-)
arm /usr/bin/apt-get "${APT[@]}" update
arm /usr/bin/apt-get "${APT[@]}" install -y --no-install-recommends python3-pyte nano
for name in launcher.py local_terminal.py zeroday-features.json ZERO-DAY-PORT.md LOCAL-CODING.md; do
    test ! -e "$R/opt/hackeros/$name" || cp -p "$R/opt/hackeros/$name" "$B/"
    install -o 0 -g 0 -m 0644 "$P/staging/opt/hackeros/$name" "$R/opt/hackeros/$name"
done
chmod 0755 "$R/opt/hackeros/launcher.py"
cp -p "$R/home/hacker/README-FIRST.txt" "$B/README-FIRST.txt"
install -o 1000 -g 1000 -m 0644 "$P/staging/README-FIRST.txt" "$R/home/hacker/README-FIRST.txt"
arm /usr/bin/python3 -c 'import sys; sys.path.insert(0,"/opt/hackeros"); import pyte,local_terminal; print("Local terminal modules import successfully")'
arm /usr/bin/apt-get clean
sync
echo 'Local terminal/keyboard staged on card. Native OpenCode/provider test required.'
