#!/usr/bin/python3
"""Guarded offline update for the existing, already provisioned handheld card."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent
STAGING = PROJECT / 'staging'
DTB = 'boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb'
DTB_SHA = 'eadca255505fba70e0da039364e633130b2d278d0475fa4ca95bf5626d28b639'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mount_uuid(path):
    return subprocess.check_output(['findmnt', '-n', '-o', 'UUID', '--mountpoint', str(path)], text=True).strip()


def safe_target(relative):
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts:
        return False
    exact = {'etc/os-release', 'etc/issue', 'etc/hackeros/release',
             'home/hacker/README-FIRST.txt', 'boot/u-boot/logo.bmp'}
    return relative in exact or relative.startswith((
        'opt/hackeros/', 'usr/local/lib/gamehack-zero/', 'usr/local/sbin/hackeros-',
        'usr/local/share/gamehack-zero/ir-database/',
        'etc/systemd/system/gamehack-sd2-'))


def install(root):
    assert os.geteuid() == 0, 'Run with pkexec/root'
    root = root.resolve(strict=True)
    manifest = json.loads((PROJECT / 'release-4.2.0.json').read_text())
    assert manifest['version'] == '4.2.0'
    assert mount_uuid(root) == manifest['target_root_uuid'], 'Wrong system card'
    assert mount_uuid(root / 'boot/u-boot') == '1A45-2972', 'Mount the correct boot partition first'
    assert sha(root / DTB) == DTB_SHA, 'Unexpected active DTB; investigate before updating'
    assert subprocess.check_output(['fdtget', '-t', 's', str(root / DTB), '/usb@ff300000', 'dr_mode'], text=True).strip() == 'host'
    for mount in (root, root / 'boot/u-boot'):
        options = subprocess.check_output(['findmnt', '-n', '-o', 'OPTIONS', '--mountpoint', str(mount)], text=True).strip().split(',')
        assert 'rw' in options, 'Mount root and boot read/write before installation'
    assert (root / 'usr/local/bin/opencode').is_file(), 'Existing OpenCode installation required'
    backup_image = PROJECT / 'backups/gamehack-zero-system-64gb-20261011-005214Z.img'
    metadata = json.loads(backup_image.with_suffix('.json').read_text())
    assert backup_image.stat().st_size == metadata['size_bytes'] == 63864569856
    assert metadata['sha256'] == '30d87b5bb7d51b6d6f3f83701fb32a1479939bbe613a9608d7f185cc49cfcd5b'
    guards = {str(p.relative_to(root)): sha(p) for p in (
        root / DTB, root / 'boot/u-boot/boot.ini', root / 'etc/fstab') if p.is_file()}
    changes = []
    targets = set()
    for record in manifest['files']:
        assert safe_target(record['target']), 'Unsafe target: ' + record['target']
        assert record['target'] not in targets, 'Duplicate target'
        targets.add(record['target'])
        source = STAGING / record['source']
        assert source.resolve().is_relative_to(STAGING.resolve())
        assert not source.is_symlink() and sha(source) == record['sha256'], 'Source changed; rebuild manifest'
        target = root / record['target']
        assert target.parent.resolve().is_relative_to(root), 'Target parent escapes mounted card'
        assert not target.is_symlink(), 'Refusing to replace target symlink: ' + str(target)
        if not target.is_file() or sha(target) != record['sha256']:
            changes.append(record)
    wants = root / 'etc/systemd/system/timers.target.wants'
    for name in ('gamehack-sd2-debug.timer', 'gamehack-sd2-state.timer'):
        link = wants / name
        assert (not link.exists() and not link.is_symlink()) or (link.is_symlink() and os.readlink(link) == '/etc/systemd/system/' + name), 'Unexpected timer link'
    required = sum((STAGING / r['source']).stat().st_size * 2 for r in changes)
    assert shutil.disk_usage(root).free > required + 256 * 1024**2, 'Insufficient update/backup space'
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    backup = root / 'opt/hackeros/update-backup' / ('release-4.2.0-' + stamp)
    backup.mkdir(parents=True, mode=0o700, exist_ok=False)
    journal = {'version': '4.2.0', 'changes': [], 'status': 'in progress'}
    for record in changes:
        target = root / record['target']
        old = backup / record['target']
        if target.exists():
            old.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, old)
        journal['changes'].append({'target': record['target'], 'previously_present': old.exists()})
        (backup / 'changes.json').write_text(json.dumps(journal, indent=2) + '\n')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + '.4.2.0-new')
        assert not temporary.exists() and not temporary.is_symlink()
        with temporary.open('xb') as stream:
            stream.write((STAGING / record['source']).read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, int(record['mode'], 8))
        if record['target'] == 'home/hacker/README-FIRST.txt':
            os.chown(temporary, 1000, 1000)
        temporary.replace(target)
        assert sha(target) == record['sha256']
    wants.mkdir(parents=True, exist_ok=True)
    for name in ('gamehack-sd2-debug.timer', 'gamehack-sd2-state.timer'):
        link = wants / name
        expected = '/etc/systemd/system/' + name
        if link.is_symlink():
            assert os.readlink(link) == expected
        else:
            assert not link.exists()
            link.symlink_to(expected)
    assert all(sha(root / relative) == digest for relative, digest in guards.items())
    assert subprocess.check_output(['fdtget', '-t', 's', str(root / DTB), '/usb@ff300000', 'dr_mode'], text=True).strip() == 'host'
    journal['status'] = 'files installed and verified; native validation pending'
    (backup / 'changes.json').write_text(json.dumps(journal, indent=2) + '\n')
    os.sync()
    print('GameHack Zero 4.2.0 installed:', len(changes), 'changed files.')
    print('Replaced-file backup:', backup)
    print('Kernel/DTB/boot configuration unchanged. Validate, unmount and safely eject.')


if __name__ == '__main__':
    install(Path(sys.argv[1] if len(sys.argv) > 1 else '/mnt/gamehack-debug'))
