"""Flipper-format remote reader and bounded GameHack waveform conversion."""
from pathlib import Path
import re

DATABASE = Path('/usr/local/share/gamehack-zero/ir-database')
MAX_FILE = 4 * 1024 * 1024


def buttons(filename):
    path = Path(filename)
    with path.open(encoding='utf-8-sig') as stream:
        text = stream.read(MAX_FILE + 1)
    if len(text) > MAX_FILE:
        raise ValueError('Remote file exceeds size limit')
    result = []
    current = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, value = (part.strip() for part in line.split(':', 1))
        if key == 'name':
            current = {'name': value}
            result.append(current)
        elif current is not None:
            current[key] = value
    return result


def number(value, bits):
    parts = value.split()
    if len(parts) != 4 or any(not re.fullmatch(r'[0-9a-fA-F]{2}', p) for p in parts):
        raise ValueError('Expected four little-endian hex bytes')
    result = int.from_bytes(bytes(int(p, 16) for p in parts), 'little')
    if result >= 1 << bits:
        raise ValueError('Protocol address/command out of range')
    return result


def waveform(button):
    if button.get('type') == 'raw':
        carrier = int(button['frequency'])
        durations = [int(p) for p in button['data'].split()]
    elif button.get('type') == 'parsed':
        protocol = button.get('protocol')
        if protocol not in ('NEC', 'NECext'):
            raise ValueError('Unsupported parsed protocol: ' + str(protocol))
        bits = 8 if protocol == 'NEC' else 16
        address = number(button['address'], bits)
        command = number(button['command'], bits)
        if protocol == 'NEC':
            payload = address | ((address ^ 255) << 8) | (command << 16) | ((command ^ 255) << 24)
        else:
            payload = address | (command << 16)
        carrier = 38000
        durations = [9000, 4500]
        for bit in range(32):
            durations.extend((560, 1690 if payload & (1 << bit) else 560))
        durations.append(560)
    else:
        raise ValueError('Unknown signal type')
    if not 10000 <= carrier <= 1000000:
        raise ValueError('Invalid carrier frequency')
    if not durations or len(durations) > 4096 or any(d < 1 or d > 2000000 for d in durations):
        raise ValueError('Invalid or oversized waveform')
    if sum(durations) > 5000000:
        raise ValueError('Waveform exceeds five seconds')
    if sum((max(1, round(d / 16)) + 126) // 127 for d in durations) > 1017:
        raise ValueError('Waveform exceeds Tiqiaa packet capacity')
    return carrier, durations


def load_button(filename, index):
    entries = buttons(filename)
    if index < 0 or index >= len(entries):
        raise ValueError('Button index out of range')
    return waveform(entries[index])
