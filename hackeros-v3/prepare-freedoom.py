#!/usr/bin/env python3
"""Verify and stage the official Freedoom 0.13.0 single-player release."""
import hashlib
import zipfile
from pathlib import Path

archive = Path("/tmp/opencode/freedoom-0.13.0.zip")
expected = "3f9b264f3e3ce503b4fb7f6bdcb1f419d93c7b546f4df3e874dd878db9688f59"
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit("Freedoom release checksum mismatch")
output = Path(__file__).resolve().parent / "staging/opt/freedoom"
output.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(archive) as bundle:
    for name in ("freedoom1.wad", "freedoom2.wad", "COPYING.txt", "README.html", "CREDITS.txt", "CREDITS-MUSIC.txt"):
        matches = [entry for entry in bundle.namelist() if Path(entry).name == name]
        if len(matches) != 1:
            raise SystemExit(f"Expected exactly one {name} in release")
        (output / name).write_bytes(bundle.read(matches[0]))
print("Official Freedoom Phase 1 + 2 staged; SHA256 matches published checksum.")
