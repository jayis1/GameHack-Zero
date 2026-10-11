#!/bin/bash

set -Eeuo pipefail

SOURCE_DISK=/dev/sda
SOURCE_ROOT=/run/media/jais/armbian
SOURCE_BOOT=/run/media/jais/BOOT
TARGET_DISK=/dev/sdb
STAGING=/home/jais/hackeros-v3/staging
WORK=/mnt/hackeros-v3-install
ROOT="$WORK/root"
BOOT="$ROOT/boot/u-boot"

die() {
    echo "ERROR: $*" >&2
    exit 1
}

unmount_target() {
    local target
    while read -r target; do
        [ -n "$target" ] && umount "$target" 2>/dev/null || true
    done < <(findmnt -rn -S "${TARGET_DISK}1" -o TARGET | sort -r)
    while read -r target; do
        [ -n "$target" ] && umount "$target" 2>/dev/null || true
    done < <(findmnt -rn -S "${TARGET_DISK}2" -o TARGET | sort -r)
}

cleanup() {
    sync || true
    mountpoint -q "$BOOT" && umount "$BOOT" || true
    mountpoint -q "$ROOT" && umount "$ROOT" || true
    rmdir "$BOOT" "$ROOT" "$WORK" 2>/dev/null || true
}
trap cleanup EXIT

[ "${EUID}" -eq 0 ] || die "Run this installer as root."
[ -b "$SOURCE_DISK" ] || die "Source disk $SOURCE_DISK is missing."
[ -b "$TARGET_DISK" ] || die "Target disk $TARGET_DISK is missing."
[ -f "$SOURCE_BOOT/boot.ini" ] || die "R36S boot files are not mounted at $SOURCE_BOOT."
[ -f "$SOURCE_ROOT/etc/os-release" ] || die "Base root filesystem is not mounted at $SOURCE_ROOT."
[ -f "$STAGING/opt/hackeros/launcher.py" ] || die "GameHack Zero v3 staging payload is incomplete."

target_size=$(blockdev --getsize64 "$TARGET_DISK")
[ "$target_size" -ge 60000000000 ] && [ "$target_size" -le 70000000000 ] \
    || die "$TARGET_DISK is not the expected 64 GB card (size: $target_size bytes)."
[ "$(lsblk -dn -o RM "$TARGET_DISK" | tr -d ' ')" = 1 ] \
    || die "$TARGET_DISK is not marked removable."

echo "Installing GameHack Zero v3 to $TARGET_DISK ..."
unmount_target

# Recreate the R36S layout. The first partition starts at sector 32768 because
# Rockchip's loader and U-Boot occupy sectors in the preceding 16 MiB gap.
wipefs --all --force "$TARGET_DISK"
sfdisk --wipe always "$TARGET_DISK" <<'EOF'
label: dos
unit: sectors

start=32768, size=524288, type=b
start=557056, type=83
EOF

# Copy the board loader without replacing the new MBR partition table.
dd if="$SOURCE_DISK" of="$TARGET_DISK" bs=512 skip=1 seek=1 count=32767 \
    iflag=fullblock conv=notrunc,fsync status=progress
partprobe "$TARGET_DISK"
udevadm settle
unmount_target

mkfs.vfat -F 32 -n BOOT "${TARGET_DISK}1"
mkfs.ext4 -F -L GAMEHACK -m 1 "${TARGET_DISK}2"
udevadm settle
unmount_target

mkdir -p "$ROOT"
mount "${TARGET_DISK}2" "$ROOT"
mkdir -p "$BOOT"
mount "${TARGET_DISK}1" "$BOOT"

echo "Copying the R36S base system ..."
rsync -aHAXx --numeric-ids --info=progress2 \
    --exclude='/boot/u-boot/***' \
    --exclude='/dev/***' --exclude='/proc/***' --exclude='/run/***' --exclude='/sys/***' \
    "$SOURCE_ROOT/" "$ROOT/"
mkdir -p "$ROOT/dev" "$ROOT/proc" "$ROOT/run" "$ROOT/sys"
rsync -rt --delete "$SOURCE_BOOT/" "$BOOT/"
if [ -f "$STAGING/boot-assets/logo.bmp" ]; then
    cp -n "$BOOT/logo.bmp" "$BOOT/logo-original.bmp"
    install -m 0644 "$STAGING/boot-assets/logo.bmp" "$BOOT/logo.bmp"
fi

echo "Applying GameHack Zero v3 ..."
rsync -a "$STAGING/etc/" "$ROOT/etc/"
rsync -a "$STAGING/opt/" "$ROOT/opt/"
rsync -a "$STAGING/usr/" "$ROOT/usr/"
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

# Preserve both USB-role device trees and make gadget mode the default.
dtb_dir="$ROOT/boot/dtb/rockchip"
cp -f "$dtb_dir/rk3326-gameconsole-r36s.dtb" \
    "$dtb_dir/rk3326-gameconsole-r36s-host.dtb"
install -m 0644 "$STAGING/rk3326-gameconsole-r36s-gadget.dtb" \
    "$dtb_dir/rk3326-gameconsole-r36s-gadget.dtb"
cp -f "$dtb_dir/rk3326-gameconsole-r36s-gadget.dtb" \
    "$dtb_dir/rk3326-gameconsole-r36s.dtb"
/bin/bash /home/jais/hackeros-v3/enable-r36xx-usb-wifi.sh "$ROOT"

boot_uuid=$(blkid -s UUID -o value "${TARGET_DISK}1")
root_uuid=$(blkid -s UUID -o value "${TARGET_DISK}2")
sed -E -i \
    -e "s#root=(LABEL|UUID)=[^ ]+( rootfstype=ext4)?#root=UUID=$root_uuid rootfstype=ext4#" \
    -e 's# rootwait rw( init=/sbin/init)?# rootwait rw init=/sbin/init#' \
    "$BOOT/boot.ini"
cat >"$ROOT/etc/fstab" <<EOF
UUID=$root_uuid / ext4 defaults,commit=120,errors=remount-ro 0 1
UUID=$boot_uuid /boot/u-boot vfat defaults 0 2
tmpfs /tmp tmpfs defaults,nosuid 0 0
EOF

mkdir -p "$ROOT/data/gamehack-zero/captures" "$ROOT/data/external" "$ROOT/home/hacker"
cp /usr/bin/qemu-aarch64-static "$ROOT/usr/bin/qemu-aarch64-static"

qemu_chroot() {
    chroot "$ROOT" /usr/bin/qemu-aarch64-static "$@"
}

if ! grep -q '^hacker:' "$ROOT/etc/passwd"; then
    qemu_chroot /usr/sbin/useradd -m -s /bin/bash \
        -G sudo,input,video,render,audio,netdev hacker
fi

password=$(openssl rand -hex 9)
printf 'hacker:%s\n' "$password" | qemu_chroot /usr/sbin/chpasswd
qemu_chroot /usr/bin/passwd --expire hacker
hacker_uid=$(awk -F: '$1=="hacker" {print $3}' "$ROOT/etc/passwd")
hacker_gid=$(awk -F: '$1=="hacker" {print $4}' "$ROOT/etc/passwd")
install -o 0 -g "$hacker_gid" -m 0640 \
    /dev/null "$ROOT/etc/hackeros/bootstrap-password"
printf '%s\n' "$password" >"$ROOT/etc/hackeros/bootstrap-password"
install -o "$hacker_uid" -g "$hacker_gid" -m 0644 \
    "$STAGING/README-FIRST.txt" "$ROOT/home/hacker/README-FIRST.txt"
chown -R "$hacker_uid:$hacker_gid" "$ROOT/home/hacker" "$ROOT/data/gamehack-zero"

echo gamehack-zero >"$ROOT/etc/hostname"
sed -i 's/^127\.0\.1\.1.*/127.0.1.1\tgamehack-zero/' "$ROOT/etc/hosts"
: >"$ROOT/etc/machine-id"
rm -f "$ROOT"/etc/ssh/ssh_host_*
rm -f "$ROOT/usr/bin/qemu-aarch64-static"

systemctl --root="$ROOT" disable serial-getty@ttyS0.service || true
systemctl --root="$ROOT" mask serial-getty@ttyS0.service

systemctl --root="$ROOT" enable \
    hackeros-gadget.service hackeros-usb-network.service \
    hackeros-storage.service hackeros-ui.service ssh.service NetworkManager.service \
    bluetooth.service

sync
echo
echo "GameHack Zero v3 installation completed successfully."
echo "Target: $TARGET_DISK"
echo "Initial user: hacker"
echo "Initial password: $password"
echo "The password is also shown in the device's SSH Instructions screen."
