#!/bin/bash
set -Eeuo pipefail
test "$EUID" -eq 0
TARGET=/dev/sda
IMAGE=/home/jais/gamehack-companion/images/raspios-lite-armhf.img
# User authorized this exact 32GB card, NOT the 64GB GameHack card.
test "$(blockdev --getsize64 "$TARGET")" = 31914983424
test "$(lsblk -dn -o RM "$TARGET")" = 1
test "$(lsblk -dn -o TRAN "$TARGET")" = usb
test "$(blkid -s UUID -o value "${TARGET}1")" = DE5B-DDAC
test "$(blkid -s UUID -o value "${TARGET}2")" = e93f253d-fe31-4b85-a33a-cd6478fa1fa0
for part in "${TARGET}1" "${TARGET}2" "${TARGET}3"; do
    ! findmnt -rn -S "$part"
done
test -s "$IMAGE"
dd if="$IMAGE" of="$TARGET" bs=4M conv=fsync status=progress
cmp -n "$(stat -c %s "$IMAGE")" "$IMAGE" "$TARGET"
partprobe "$TARGET"
udevadm settle
echo 'Base image written and byte-for-byte read-back verified on the authorized 32GB card.'
