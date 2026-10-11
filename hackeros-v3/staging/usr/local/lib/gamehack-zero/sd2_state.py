#!/usr/bin/python3
"""Read standard kernel SD2 diagnostics; never reset or reconfigure hardware."""
from pathlib import Path

LIMIT = 16384


def clock_command(value):
    return {'clock_update': bool(value & (1 << 21)),
            'wait_previous_data': bool(value & (1 << 13)),
            'start_pending': bool(value & (1 << 31))}


def read(path, limit=LIMIT):
    try:
        with path.open() as stream:
            return stream.read(limit)
    except OSError as exc:
        return 'Unavailable: ' + str(exc) + '\n'


def hosts(root=Path('/')):
    result = []
    for path in (root / 'sys/class/mmc_host').glob('mmc*'):
        # Match physical SD2 controller, not unstable mmc numbering.
        if any('ff380000' in part for part in (path / 'device').resolve().parts):
            result.append(path.name)
    return result


def report(root=Path('/')):
    sections = ['GameHack SD2 controller diagnostics (no forced reset/rescan)',
                'Boot: ' + read(root / 'proc/sys/kernel/random/boot_id').strip(),
                'Logged command 0x202000 flags: ' + str(clock_command(0x202000)),
                'The driver reports a clock-update timeout, not a card CMD0 response.']
    selected = hosts(root)
    sections.append('ff380000 hosts: ' + (', '.join(selected) or 'NONE'))
    for name in selected:
        for file in ('ios', 'regs', 'state'):
            sections.append(name + '/' + file + '\n' + read(root / 'sys/kernel/debug' / name / file))
    for relative, keywords in [
        ('sys/kernel/debug/clk/clk_summary', ('sdio', 'gpll', 'cpll', 'npll', 'xin24m')),
        ('sys/kernel/debug/regulator/regulator_summary', ('vcc_sd', 'vccio_sd', 'ff380000')),
    ]:
        data = read(root / relative, 524288)
        lines = [line for line in data.splitlines() if any(word in line.lower() for word in keywords)]
        if data.startswith('Unavailable:'):
            lines = [data]
        sections.append(relative + '\n' + '\n'.join(lines)[:LIMIT])
    return '\n\n'.join(sections)[:65536]


if __name__ == '__main__':
    print(report())
