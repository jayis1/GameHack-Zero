#!/usr/bin/python3
"""Read-only USB/driver diagnostics; no radio resets or role changes."""
import subprocess


def command(args):
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=5)
        return (result.stdout + result.stderr).strip()[-8000:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc)


def diagnosis(devices, kernel):
    if any('wifi' in line.lower() for line in devices.splitlines()):
        return 'Linux detects a Wi-Fi interface. Check connection/rfkill state below.'
    if 'error -71' in kernel or 'unable to enumerate USB device' in kernel:
        return 'USB enumeration failed in this boot. The device could not identify itself; this is not proof of a missing Wi-Fi driver. Unplug Pi/converter, fully power off, then test Wi-Fi alone.'
    if 'failed to read EFuse' in kernel:
        return 'The Wi-Fi driver saw a USB device but could not read its hardware data. Check USB power/wiring before replacing the driver.'
    if 'firmware' in kernel.lower() and ('failed' in kernel.lower() or 'not found' in kernel.lower()):
        return 'A firmware-loading error was logged. Inspect the exact filename below.'
    return 'No Wi-Fi interface detected. Check USB detection, driver and firmware evidence below; the cause is not established.'


if __name__ == '__main__':
    devices = command(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'dev', 'status'])
    kernel = command(['journalctl', '-k', '-b', '--no-pager', '-n', '55', '--grep', 'usb .*error -|unable to enumerate|failed to read EFuse|rtl8xxxu|rtw88|firmware.*(failed|not found)'])
    print(diagnosis(devices, kernel))
    for title, output in [('DEVICES', devices), ('USB DEVICES', command(['lsusb'])),
                          ('RADIO BLOCKS', command(['rfkill', 'list'])),
                          ('RTL8188EU DRIVER', command(['modinfo', '-F', 'filename', 'rtl8xxxu'])),
                          ('USB / DRIVER LOG', kernel)]:
        print('\n' + title + '\n' + output)
