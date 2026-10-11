#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-debug
P=/home/jais/hackeros-v3
test "$EUID" -eq 0
test "$(findmnt -n -o UUID --mountpoint "$R")" = 2ac15f87-aa0e-4fa6-9437-b542636d070c
DTB="$R/boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb"
before="$(sha256sum "$DTB" | awk '{print $1}')"
test -d "$P/staging/usr/local/share/gamehack-zero/ir-database"
target="$R/usr/local/share/gamehack-zero/ir-database"
test ! -e "$target" || { echo 'Existing database found; refusing to overwrite it.'; exit 1; }
mount -o remount,rw "$R"
B="$R/opt/hackeros/update-backup/ir-database-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B"
for file in opt/hackeros/launcher.py opt/hackeros/ir_library.py usr/local/lib/gamehack-zero/ir_database.py usr/local/lib/gamehack-zero/tiqiaa_ir.py usr/local/sbin/hackeros-action; do
    if [ -e "$R/$file" ]; then
        install -d "$B/$(dirname "$file")"
        cp -p "$R/$file" "$B/$file"
    fi
    mode=0644
    case "$file" in usr/local/sbin/*|opt/hackeros/launcher.py|usr/local/lib/gamehack-zero/tiqiaa_ir.py) mode=0755 ;; esac
    install -D -m "$mode" "$P/staging/$file" "$R/$file"
done
install -d "$(dirname "$target")"
cp -a "$P/staging/usr/local/share/gamehack-zero/ir-database" "$target"
chown -R root:root "$target"
find "$target" -type d -exec chmod 0755 {} +
find "$target" -type f -exec chmod 0644 {} +
python3 - "$P/staging/usr/local/share/gamehack-zero/ir-database" "$target" <<'PY'
from pathlib import Path
import hashlib
import sys
source, target = map(Path, sys.argv[1:])
for path in source.rglob('*'):
    if path.is_file():
        copied = target / path.relative_to(source)
        assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(copied.read_bytes()).digest(), str(copied)
print('Every database file verified byte-for-byte.')
PY
install -m 0644 "$P/IR-DATABASE.md" "$R/opt/hackeros/IR-DATABASE.md"
test "$before" = "$(sha256sum "$DTB" | awk '{print $1}')"
sync
echo 'GameHack Zero IR database installed; active DTB unchanged.'
