#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0
ROOT=/mnt/gamehack-pi
PROJECT=/home/jais/gamehack-companion
test "$(findmnt -n -o UUID "$ROOT")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test "$(findmnt -n -o UUID "$ROOT/boot/firmware")" = DA0C-EC97
test ! -e "$ROOT/usr/bin/qemu-arm-static"
install -m 0755 /usr/bin/qemu-arm-static "$ROOT/usr/bin/qemu-arm-static"
trap 'rm -f "$ROOT/usr/bin/qemu-arm-static"' EXIT
arm() { chroot "$ROOT" /usr/bin/qemu-arm-static "$@"; }
export QEMU_CPU=arm1176
ulimit -c 0
arm /usr/bin/python3 -c 'print("Target ARMv6 Python verified")'
arm /usr/sbin/useradd -m -s /bin/bash companion
while IFS= read -r -d '' file; do
    relative=${file#"$PROJECT/staging/"}
    mode=0644
    case "$relative" in
        usr/local/bin/*|usr/local/sbin/*) mode=0755 ;;
        etc/NetworkManager/system-connections/*) mode=0600 ;;
        etc/sudoers.d/*) mode=0440 ;;
    esac
    install -D -o 0 -g 0 -m "$mode" "$file" "$ROOT/$relative"
done < <(find "$PROJECT/staging" -type f -print0)
UID_PI=$(awk -F: '$1=="companion" {print $3}' "$ROOT/etc/passwd")
GID_PI=$(awk -F: '$1=="companion" {print $4}' "$ROOT/etc/passwd")
install -d -o "$UID_PI" -g "$GID_PI" -m 0700 "$ROOT/home/companion/.ssh"
install -o "$UID_PI" -g "$GID_PI" -m 0600 "$PROJECT/access/gamehack-pi-ed25519.pub" "$ROOT/home/companion/.ssh/authorized_keys"
install -d -o "$UID_PI" -g "$GID_PI" -m 0750 "$ROOT/home/companion/shared"
install -o "$UID_PI" -g "$GID_PI" -m 0644 "$PROJECT/README.md" "$ROOT/home/companion/README.md"
printf 'gamehack-companion\n' > "$ROOT/etc/hostname"
sed -i 's/raspberrypi/gamehack-companion/g' "$ROOT/etc/hosts"
printf '\n# GameHack Companion: Pi Zero W USB Ethernet device\n[all]\ndtoverlay=dwc2,dr_mode=peripheral\n' >> "$ROOT/boot/firmware/config.txt"
python3 - "$ROOT/boot/firmware/cmdline.txt" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
args = [x for x in path.read_text().split() if x != 'resize']
args.append('modules-load=dwc2,g_ether')
path.write_text(' '.join(args) + '\n')
PY
touch "$ROOT/etc/cloud/cloud-init.disabled"
systemctl --root="$ROOT" mask userconfig.service regenerate_ssh_host_keys.service ssh.socket
systemctl --root="$ROOT" enable NetworkManager.service ssh.service gamehack-usb-dhcp.service
# Fresh keys must remain stable so the GameHack can pin the Pi's identity.
ssh-keygen -q -t ed25519 -N '' -C gamehack-companion-host -f "$ROOT/etc/ssh/ssh_host_ed25519_key"
arm /usr/bin/ssh-keygen -A
awk '{print "192.168.77.1,gamehack-companion.local " $1 " " $2}' "$ROOT/etc/ssh/ssh_host_ed25519_key.pub" > "$PROJECT/access/known_hosts"
chown 1000:1000 "$PROJECT/access/known_hosts"
chmod 0600 "$PROJECT/access/known_hosts"
install -d -m 0755 "$ROOT/run/sshd"
arm /usr/sbin/sshd -t
arm /usr/sbin/visudo -c
arm /usr/sbin/dnsmasq --test --conf-file=/etc/gamehack-usb-dhcp.conf
arm /usr/bin/python3 /usr/local/bin/gamehack-companion status
arm /usr/bin/python3 -m py_compile /usr/local/bin/gamehack-companion
sync
echo 'GameHack Companion configured; USB boot/connectivity still requires the actual Pi.'
