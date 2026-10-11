#!/usr/bin/python3
"""Bounded, unprivileged SD2 diagnostics; no commands, secrets or captures copied."""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

DEBUG_UUID = 'db0e4472-ba23-4523-9b61-2f9694211ce4'
DEBUG_UUIDS = {DEBUG_UUID, '83809ff4-9ea9-46b0-bec0-14b719a09e61'}
LIMIT = 65536
KEEP = 20


def command(args):
    # Command output is collected in a temporary file, not unlimited RAM.
    with tempfile.TemporaryFile() as output:
        try:
            result = subprocess.run(args, stdout=output, stderr=subprocess.STDOUT, timeout=6)
            output.seek(0)
            return output.read(LIMIT).decode(errors='replace') + f'\nexit={result.returncode}\n'
        except (OSError, subprocess.TimeoutExpired) as exc:
            return str(exc) + '\n'


def mounted(root):
    values = command(['findmnt', '-n', '-o', 'UUID', '--mountpoint', str(root)]).splitlines()
    return bool(values) and values[0] in DEBUG_UUIDS


def write(path, text):
    if path.is_symlink():
        raise ValueError('Refusing symlink in diagnostic storage')
    fd, temporary = tempfile.mkstemp(prefix='.snapshot-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text[:LIMIT])
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def prune(folder, current):
    # Only remove files this collector owns, not user-created debug folders.
    names = {'kernel.txt', 'network.txt', 'hardware.txt', 'services.txt', 'pi-link.json'}
    sessions = sorted((p for p in folder.iterdir() if re.fullmatch(r'boot-[0-9a-f-]{36}', p.name)
                       and p.is_dir() and not p.is_symlink() and p != current),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    for path in sessions[KEEP - 1:]:
        for name in names:
            file = path / name
            if file.is_file() and not file.is_symlink():
                file.unlink()
        if not any(path.iterdir()):
            path.rmdir()


def collect(root=Path('/data/debug')):
    if not mounted(root):
        return False  # Never spill SD2 reports onto the 64GB root filesystem.
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    if not re.fullmatch(r'[0-9a-f-]{36}', boot):
        raise ValueError('Invalid boot ID')
    sessions = root / 'sessions'
    if sessions.is_symlink():
        raise ValueError('Refusing symlink sessions directory')
    sessions.mkdir(mode=0o700, exist_ok=True)
    current = sessions / ('boot-' + boot)
    if current.is_symlink():
        raise ValueError('Refusing symlink boot directory')
    current.mkdir(mode=0o700, exist_ok=True)
    reports = {
        'kernel.txt': ['journalctl', '-k', '-b', '--no-pager', '-n', '400'],
        'network.txt': ['sh', '-c', 'ip -brief address; ip route; rfkill list; nmcli -f DEVICE,TYPE,STATE device status'],
        'hardware.txt': ['sh', '-c', 'date -Is; uname -a; lsusb; lsusb -t; lsblk -o NAME,SIZE,FSTYPE,LABEL,UUID,MOUNTPOINTS'],
        'services.txt': ['systemctl', 'show', 'hackeros-ui', 'NetworkManager', 'ssh', 'hackeros-storage',
                         '-p', 'Id', '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result'],
    }
    for name, args in reports.items():
        if not mounted(root):
            return False
        write(current / name, command(args))
    pi = Path('/data/gamehack-zero/pi-last-connection.json')
    if pi.is_file() and not pi.is_symlink():
        try:
            with pi.open() as stream:
                data = json.loads(stream.read(LIMIT))
            if not isinstance(data, dict):
                data = {}
        except (OSError, ValueError):
            data = {'reason': 'Pi diagnostic metadata is unreadable; inspect system-card logs'}
        # Copy only the diagnostic client's metadata, never task output.
        filtered = {key: data[key] for key in ('timestamp', 'action', 'exit_code', 'reason', 'paired_usb_interfaces') if key in data}
        if mounted(root):
            write(current / 'pi-link.json', json.dumps(filtered, indent=2) + '\n')
    prune(sessions, current)
    return True


if __name__ == '__main__':
    collect()
