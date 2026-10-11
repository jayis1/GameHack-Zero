#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
P=/home/jais/gamehack-companion
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test "$(findmnt -n -o UUID "$R/boot/firmware")" = DA0C-EC97
test -f "$R/lib/modules/6.18.50+rpt-rpi-v6/kernel/drivers/usb/gadget/function/usb_f_ncm.ko.xz"
test ! -e "$R/etc/systemd/system/gamehack-usb-ncm.service"
grep -q 'modules-load=dwc2,g_ether' "$R/boot/firmware/cmdline.txt"
mount -o remount,rw "$R"
mount -o remount,rw "$R/boot/firmware"
B="$R/opt/gamehack-worker-backup/ncm-test-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
cp -p "$R/boot/firmware/cmdline.txt" "$B/cmdline.txt"
cp -p "$R/etc/modules-load.d/gamehack-usb.conf" "$B/modules-load.conf"
journalctl --directory="$R/var/log/journal" -b 0 --no-pager > "$B/last-ecm-boot.txt"
python3 - "$R" <<'PY'
from pathlib import Path
import sys
r=Path(sys.argv[1])
path=r/'boot/firmware/cmdline.txt'
text=path.read_text()
assert text.count('modules-load=dwc2,g_ether')==1
path.write_text(text.replace('modules-load=dwc2,g_ether', 'modules-load=dwc2'))
path=r/'etc/modules-load.d/gamehack-usb.conf'
lines=path.read_text().splitlines()
path.write_text('\n'.join(line for line in lines if line.strip()!='g_ether')+'\n')
PY
install -m 0755 "$P/staging/usr/local/sbin/gamehack-usb-ncm" "$R/usr/local/sbin/gamehack-usb-ncm"
install -m 0644 "$P/staging/etc/systemd/system/gamehack-usb-ncm.service" "$R/etc/systemd/system/gamehack-usb-ncm.service"
ln -s /etc/systemd/system/gamehack-usb-ncm.service "$R/etc/systemd/system/multi-user.target.wants/gamehack-usb-ncm.service"
cat > "$B/rollback.sh" <<'ROLLBACK'
#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
B="$(dirname "$(readlink -f "$0")")"
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test "$(findmnt -n -o UUID "$R/boot/firmware")" = DA0C-EC97
mount -o remount,rw "$R"
mount -o remount,rw "$R/boot/firmware"
cp -p "$B/cmdline.txt" "$R/boot/firmware/cmdline.txt"
cp -p "$B/modules-load.conf" "$R/etc/modules-load.d/gamehack-usb.conf"
test ! -L "$R/etc/systemd/system/multi-user.target.wants/gamehack-usb-ncm.service" || unlink "$R/etc/systemd/system/multi-user.target.wants/gamehack-usb-ncm.service"
sync
echo 'Original g_ether boot path restored. NCM service remains installed but disabled.'
ROLLBACK
chmod 0700 "$B/rollback.sh"
install -m 0644 "$P/NCM-TEST.md" "$R/opt/NCM-TEST.md"
sync
echo "Experimental NCM path installed. Backup and rollback script: $B"
