#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
P=/home/jais/gamehack-companion
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
mount -o remount,rw "$R"
test ! -e "$R/usr/bin/qemu-arm-static"
test ! -e "$R/usr/sbin/policy-rc.d"
install -m 0755 /usr/bin/qemu-arm-static "$R/usr/bin/qemu-arm-static"
printf '#!/bin/sh\nexit 101\n' > "$R/usr/sbin/policy-rc.d"
chmod 0755 "$R/usr/sbin/policy-rc.d"
mount --bind /dev "$R/dev"
mount -t proc proc "$R/proc"
cleanup() {
    umount "$R/proc"
    umount "$R/dev"
    rm -f "$R/usr/bin/qemu-arm-static" "$R/usr/sbin/policy-rc.d"
}
trap cleanup EXIT
ulimit -c 0
export QEMU_CPU=arm1176
arm() { chroot "$R" /usr/bin/qemu-arm-static "$@"; }
arm /usr/bin/apt-get update
arm /usr/bin/apt-get install -y --no-install-recommends tcpdump
B="$R/opt/gamehack-worker-backup/$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
cp -p "$R/usr/local/bin/gamehack-companion" "$B/"
for relative in usr/local/bin/gamehack-companion usr/local/lib/gamehack-worker.py usr/local/sbin/gamehack-radio etc/systemd/system/gamehack-worker.service etc/sudoers.d/gamehack-radio; do
    mode=0644
    case "$relative" in usr/local/bin/*|usr/local/sbin/*) mode=0755 ;; etc/sudoers.d/*) mode=0440 ;; esac
    install -D -o 0 -g 0 -m "$mode" "$P/staging/$relative" "$R/$relative"
done
arm /usr/sbin/visudo -c
arm /usr/bin/python3 -m py_compile /usr/local/lib/gamehack-worker.py /usr/local/sbin/gamehack-radio /usr/local/bin/gamehack-companion
systemctl --root="$R" enable gamehack-worker.service bluetooth.service
arm /usr/bin/apt-get clean
sync
echo 'Worker queue and capability-checked radio actions installed; native radio/USB tests still required.'
