#!/bin/bash
set -Eeuo pipefail
R=/mnt/gamehack-pi
P=/home/jais/gamehack-companion
test "$EUID" -eq 0
test "$(findmnt -n -o UUID "$R")" = 5a4bdad1-138b-490f-b9a9-0bf50cb3847d
test "$(findmnt -n -o UUID "$R/boot/firmware")" = DA0C-EC97
mount -o remount,rw "$R"
B="$R/opt/gamehack-worker-backup/boot-errors-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$B/journals"
journalctl --directory="$R/var/log/journal" --no-pager > "$B/readable-journal.txt"
cp -p "$R/etc/systemd/system/ssh.service.d/gamehack.conf" "$B/ssh-gamehack.conf"
cp -p "$R/etc/systemd/journald.conf.d/gamehack.conf" "$B/journald-gamehack.conf"
install -m 0644 "$P/staging/etc/systemd/system/ssh.service.d/gamehack.conf" "$R/etc/systemd/system/ssh.service.d/gamehack.conf"
install -m 0644 "$P/staging/etc/systemd/journald.conf.d/gamehack.conf" "$R/etc/systemd/journald.conf.d/gamehack.conf"
# Preserve damaged binary journals outside the active journal directory,
# together with the readable export. No evidence or healthy journal is deleted.
while IFS= read -r -d '' file; do
    if ! journalctl --verify --file="$file" > "$B/verify-$(basename "$file").txt" 2>&1; then
        mv "$file" "$B/journals/"
    fi
done < <(find "$R/var/log/journal" -type f \( -name '*.journal' -o -name '*.journal~' \) -print0)
python3 - "$R" "$B" <<'PY'
from pathlib import Path
import sys, shutil
r, backup = map(Path, sys.argv[1:])
source = r / 'usr/lib/udev/rules.d/90-alsa-restore.rules'
text = source.read_text()
# The package incorrectly labels both branches as alsa_restore_go. Restore
# the standard branch label via an /etc override without changing package data.
if text.count('LABEL="alsa_restore_go"') == 2 and 'LABEL="alsa_restore_std"' not in text:
    position = text.rfind('LABEL="alsa_restore_go"')
    text = text[:position] + text[position:].replace('LABEL="alsa_restore_go"', 'LABEL="alsa_restore_std"', 1)
    target = r / 'etc/udev/rules.d/90-alsa-restore.rules'
    if target.exists():
        if target.read_text() != text:
            raise SystemExit('Existing ALSA override differs; refusing to overwrite it')
    else:
        shutil.copy2(source, backup / '90-alsa-restore.rules')
        target.write_text(text)
        target.chmod(0o644)
PY
sync
echo "Boot error repairs installed; journal evidence preserved at $B"
