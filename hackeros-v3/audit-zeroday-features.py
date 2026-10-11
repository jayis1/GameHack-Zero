#!/usr/bin/env python3
"""Inventory upstream features without executing or blindly installing scripts."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

REFERENCE = Path('/home/jais/zero-day-os-reference')
OUTPUT = Path(__file__).parent / 'staging/opt/hackeros'
ADAPTED = {
    'wifi-scan': 'Controller Wi-Fi scan/connect; no hardcoded wlan0.',
    'wifi-monitor-toggle': 'Dedicated external-adapter passive capture; restores temporary interface.',
    'dongle-setup': 'RTL8821CU driver and capability checks; native loading still needs testing.',
    'bt-scan': 'Bounded Bluetooth discovery; hardware support remains unverified.',
    'ir-scan': 'Tiqiaa USB raw IR learning; original Cardputer GPIO IR is not used.',
    'ir-replay': 'Raw IR replay with the supported USB device; native testing required.',
    'doom-play': 'Freedoom Phase 1/2 with controller bridge and audio-contention fix.',
    'cardputer-battery': 'Linux power-supply readings, not Cardputer BQ27220 registers.',
    'cardputer-wifi-connect': 'NetworkManager controller Wi-Fi setup.',
    'cardputer-wifi-setup': 'NetworkManager controller Wi-Fi setup.',
    'cardputer-wifi-toggle': 'Allowlisted Wi-Fi enable action; USB faults are not bypassed.',
    'power-mode': 'Existing handheld power profiles; no Pi-specific CPU hotplug copied.',
    'net-discover': 'Existing authorized local-network discovery.',
    'net-quickscan': 'Existing user-confirmed target scanning; not every upstream preset.',
    'usb-gadget-mode': 'Existing host/network-role controls; not all HID/storage modes.',
    'opencode-ask': 'Cancelable quick-prompt client already deployed.',
}
HARDWARE = {'camera', 'mesh', 'hardware'}
REVIEW = {'panic', 'engagement-clean', 'post-harvest', 'exfil-discord', 'exfil-dns',
          'wifi-deauth', 'wifi-autocrack', 'wifi-evil-twin', 'wifi-karma-ap',
          'wps-attack', 'bt-attack', 'ble-spam', 'captive-portal', 'dhcp-attack',
          'pass-spray', 'kerberoast', 'quick-c2', 'ntlmrelayx', 'payload-craft',
          'arpspoof', 'ragnar-ctl', 'ragnar-scan'}


def main():
    revision = subprocess.check_output(['git', '-C', str(REFERENCE), 'rev-parse', 'HEAD'], text=True).strip()
    scripts = []
    for path in sorted((REFERENCE / 'scripts').rglob('*')):
        if not path.is_file() or path.suffix == '.md':
            continue
        name, category = path.name, path.relative_to(REFERENCE / 'scripts').parts[0]
        status, note = 'pending port', 'Needs source/dependency review and a controller workflow; not installed.'
        if category in ('nfc', 'subghz'):
            status, note = 'excluded', 'User explicitly excluded NFC and Sub-GHz.'
        elif name in ADAPTED:
            status, note = 'adapted subset', ADAPTED[name]
        elif name == 'opencode-session':
            status, note = 'implemented frontend', 'Local interactive OpenCode PTY with 112px coding-keyboard dock; native OpenCode/provider execution still needs testing.'
        elif name in REVIEW:
            status, note = 'needs scoped review', 'Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation.'
        elif category in HARDWARE or name in ('tamper-watch', 'zeroday-boot', 'zeroday-bootanim', 'zeroday-secureboot'):
            status, note = 'hardware-dependent', 'Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated.'
        scripts.append({'name': name, 'category': category, 'source': str(path.relative_to(REFERENCE)),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'status': status, 'note': note})
    tree = ast.parse((REFERENCE / 'tui/cyber_launcher.py').read_text())
    tools = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'TOOLS' for target in node.targets))
    components = [{'name': name, 'source': name + '/src', 'status': 'pending architecture-specific port'} for name in ('compositor', 'terminal', 'explorer', 'trail')]
    data = {'source': 'https://github.com/jayis1/Zero-Day-OS-', 'revision': revision,
            'scripts': scripts, 'upstream_menu_tools': tools, 'components': components}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'zeroday-features.json').write_text(json.dumps(data, indent=2) + '\n')
    lines = ['# Zero-Day OS to GameHack Zero feature map', '', 'Source revision: `' + revision + '`.', '',
             'This is an inventory and port backlog, not a claim that all upstream scripts are installed.',
             'Do not mix Kali rolling repositories into the working Debian handheld or copy Raspberry Pi boot overlays.', '',
             '| Group | Feature | Status | Handheld adaptation |', '|---|---|---|---|']
    for item in scripts:
        lines.append(f"| {item['category']} | {item['name']} | {item['status']} | {item['note']} |")
    lines += ['', '## Other components', '',
              '- Compositor: retain working Pygame/KMS display for now; no HDMI/ST7789/Cardputer keyboard assumptions.',
              '- Terminal: original local PTY/controller terminal staged with a shallow coding keyboard.',
              '- Explorer: existing browse/search are a subset; copy/move/rename/archive/hex/bookmarks remain pending.',
              '- Trail: Wi-Fi breadcrumb storage/navigation remains pending; never imply GPS/IMU direction without hardware.',
              '- Media/YouTube/Jellyfin/RetroArch: pending packages and controller/display/audio integration; no copyrighted ROMs.',
              '- Security/lock/encryption: pending explicit design; no destructive panic wiping or broad root remote shell.',
              '- Mesh/NFC/Sub-GHz/camera/MonsterC5/Grove: cannot be claimed without hardware; NFC/Sub-GHz excluded.',
              '', f'Inventory: {len(scripts)} script files; {sum(len(group) for group in tools.values())} upstream menu entries.']
    (OUTPUT / 'ZERO-DAY-PORT.md').write_text('\n'.join(lines) + '\n')
    print(lines[-1])


if __name__ == '__main__':
    main()
