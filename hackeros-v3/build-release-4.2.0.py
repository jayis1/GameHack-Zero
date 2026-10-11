#!/usr/bin/python3
"""Create a checksum manifest for the limited, credential-free release payload."""
import hashlib
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
STAGING = PROJECT / 'staging'


def payload():
    files = set()
    for pattern in ('opt/hackeros/*.py', 'opt/hackeros/*.md', 'opt/hackeros/nimbus-docs/*.md',
                    'usr/local/lib/gamehack-zero/*.py', 'usr/local/sbin/hackeros-*',
                    'usr/local/share/gamehack-zero/ir-database/**/*'):
        files.update(p for p in STAGING.glob(pattern) if p.is_file())
    for relative in ('opt/hackeros/zeroday-features.json', 'os-release', 'issue',
                     'README-FIRST.txt', 'etc/hackeros/release', 'boot-assets/logo.bmp',
                     'etc/systemd/system/gamehack-sd2-debug.service',
                     'etc/systemd/system/gamehack-sd2-debug.timer',
                     'etc/systemd/system/gamehack-sd2-state.service',
                     'etc/systemd/system/gamehack-sd2-state.timer'):
        files.add(STAGING / relative)
    records = []
    mapping = {'os-release': 'etc/os-release', 'issue': 'etc/issue',
               'README-FIRST.txt': 'home/hacker/README-FIRST.txt',
               'boot-assets/logo.bmp': 'boot/u-boot/logo.bmp'}
    for path in sorted(files):
        assert path.is_file() and not path.is_symlink(), str(path)
        relative = path.relative_to(STAGING).as_posix()
        target = mapping.get(relative, relative)
        executable = target.startswith('usr/local/sbin/') or target == 'opt/hackeros/launcher.py'
        records.append({'source': relative, 'target': target,
                        'mode': '0755' if executable else '0644',
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'version': '4.2.0', 'target_root_uuid': '2ac15f87-aa0e-4fa6-9437-b542636d070c',
            'files': records}


if __name__ == '__main__':
    manifest = payload()
    destination = PROJECT / 'release-4.2.0.json'
    destination.write_text(json.dumps(manifest, indent=2) + '\n')
    print('Release 4.2.0:', len(manifest['files']), 'verified payload files;', destination)
