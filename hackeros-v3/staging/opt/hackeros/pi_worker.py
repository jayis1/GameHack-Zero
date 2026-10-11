#!/usr/bin/env python3
"""Unprivileged, key-pinned SSH client for the paired Pi worker."""
import argparse
import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

PAIRING = Path('/home/hacker/.ssh/gamehack-pi')
HOST = 'companion@192.168.77.1'


def usb_links(root=Path('/sys/class/net')):
    result = []
    for path in root.glob('*'):
        try:
            if (path / 'address').read_text().strip().lower() == '02:47:48:50:49:02':
                result.append(path.name)
        except OSError:
            pass
    return result


def error_reason(output):
    if 'Permission denied' in output:
        return 'Pi rejected SSH authentication. Keep host-key checking enabled; verify the paired account/key on the Pi.'
    if 'Host key verification failed' in output or 'REMOTE HOST IDENTIFICATION HAS CHANGED' in output:
        return 'Pi host identity mismatch. Verify the Pi card/key; do not disable host-key checking.'
    if 'Connection refused' in output:
        return 'Pi address was reached but SSH refused the connection. Check the Pi SSH service and its boot logs.'
    if 'timed out' in output.lower():
        return 'Pi connection timed out. Check USB address/profile, Pi power, data cable and boot logs.'
    return 'Pi request failed. Inspect the screen output; USB Ethernet must enumerate before SSH works.'


def save_diagnostic(action, code, reason, links, folder=Path('/data/gamehack-zero')):
    # Do not persist user task commands, task output, provider secrets or keys.
    data = {'timestamp': time.time(), 'action': action, 'exit_code': code,
            'reason': reason, 'paired_usb_interfaces': links}
    folder.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.pi-link-', dir=folder)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
        os.replace(name, folder / 'pi-last-connection.json')
    finally:
        if os.path.exists(name):
            os.unlink(name)


def ssh_args(action, task=None, pairing=PAIRING):
    if action not in ('status', 'files', 'shutdown', 'reboot', 'task'):
        raise ValueError('Unknown Pi worker action')
    if action == 'task':
        if not task or len(task) > 2048 or '\x00' in task:
            raise ValueError('Enter a task command of at most 2048 characters')
        remote = shlex.join(['sh', '-lc', task])
    else:
        remote = shlex.join(['gamehack-companion', action])
    return ['ssh', '-T', '-i', str(pairing / 'id_ed25519'),
            '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
            '-o', 'StrictHostKeyChecking=yes', '-o', 'HostKeyAlgorithms=ssh-ed25519',
            '-o', 'UserKnownHostsFile=' + str(pairing / 'known_hosts'),
            '-o', 'ConnectTimeout=8', '-o', 'ServerAliveInterval=5',
            '-o', 'ServerAliveCountMax=2', HOST, remote]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['link', 'status', 'files', 'shutdown', 'reboot', 'task'])
    parser.add_argument('task', nargs='?')
    args = parser.parse_args()
    links = usb_links()
    if args.action == 'link':
        print('Paired Pi USB interfaces: ' + (', '.join(links) or 'NONE'))
        print('Expected USB MAC: 02:47:48:50:49:02; Pi 192.168.77.1; GameHack 192.168.77.2')
        for name in links:
            result = subprocess.run(['nmcli', '-f', 'GENERAL,IP4', 'dev', 'show', name], capture_output=True, text=True, timeout=10)
            print(result.stdout + result.stderr)
        reason = 'Paired USB interface detected' if links else 'No paired USB Ethernet device. Check Pi data port, cable, power and USB -71 errors. A converter is not a hub.'
        print(reason)
        save_diagnostic('link', 0 if links else 1, reason, links)
        return 0 if links else 1
    if not links:
        reason = 'No paired Pi USB Ethernet interface detected. This is before SSH/authentication. Check the Pi USB/data port, power, cable and USB enumeration errors.'
        print(reason)
        save_diagnostic(args.action, 1, reason, links)
        return 1
    if not (PAIRING / 'id_ed25519').is_file() or not (PAIRING / 'known_hosts').is_file():
        print('Pi worker is not paired: dedicated SSH key and pinned host identity required.')
        return 1
    try:
        command = ssh_args(args.action, args.task)
        # TemporaryFile bounds memory use for chatty worker tasks.
        with tempfile.TemporaryFile() as output:
            try:
                result = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, timeout=35)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
                print('Pi task connection timed out. The remote task may still be running.')
            output.seek(0)
            text = output.read(12000).decode(errors='replace')
            print(text)
            reason = error_reason(text) if code else 'Paired Pi request completed successfully'
            save_diagnostic(args.action, code, reason, links)
            if code == 255:
                print(reason)
            return code
    except (ValueError, OSError) as exc:
        print('Pi worker error:', exc)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
