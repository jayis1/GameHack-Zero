#!/usr/bin/env python3
"""Stage upstream USB/chip modules against the installed 6.12.32 headers."""
import concurrent.futures
import json
import shutil
import subprocess
import urllib.request
from pathlib import Path

work = Path('/tmp/opencode/gamehack-rtl8821cu')
work.mkdir(parents=True, exist_ok=True)
headers = work / 'headers'
source = work / 'source'
source.mkdir(exist_ok=True)
project = Path(__file__).resolve().parent
shutil.copyfile(project / 'driver-build/rtl8821cu/Makefile', source / 'Makefile')
shutil.copyfile(project / 'driver-build/rtl8821cu/clang-arm64', work / 'clang-arm64')
(work / 'clang-arm64').chmod(0o755)
if not headers.exists():
    shutil.copytree('/mnt/gamehack-debug/usr/src/linux-headers-6.12.32-lts-rk3326', headers)
url = 'https://api.github.com/repos/gregkh/linux/contents/drivers/net/wireless/realtek/rtw88?ref=v6.12.32'
request = urllib.request.Request(url, headers={'User-Agent': 'GameHack-driver-build'})
entries = json.load(urllib.request.urlopen(request, timeout=60))
names = {'usb.c', 'rtw8821c.c', 'rtw8821cu.c', 'rtw8821c_table.c'}
files = [entry for entry in entries if entry['name'].endswith('.h') or entry['name'] in names]
def download(entry):
    with urllib.request.urlopen(entry['download_url'], timeout=60) as response:
        (source / entry['name']).write_bytes(response.read())
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(download, files))
subprocess.run(['gcc', '-O2', '-I' + str(headers / 'scripts/include'), '-o', str(headers / 'scripts/basic/fixdep'), str(headers / 'scripts/basic/fixdep.c')], check=True)
mod = headers / 'scripts/mod'
subprocess.run(['gcc', '-O2', '-I' + str(mod), '-I' + str(headers / 'scripts/include'), '-o', str(mod / 'modpost')] + [str(mod / name) for name in ('modpost.c', 'file2alias.c', 'sumversion.c', 'symsearch.c')], check=True)
print(f'Driver sources and host build tools prepared in {work}')
