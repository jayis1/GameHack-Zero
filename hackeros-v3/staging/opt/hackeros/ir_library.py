"""Controller-friendly browsing helpers, without USB access."""
import sys
from pathlib import Path

sys.path.insert(0, '/usr/local/lib/gamehack-zero')
from ir_database import DATABASE, buttons, waveform


def entries(folder):
    return sorted((p for p in Path(folder).iterdir() if p.is_dir() or p.suffix.lower() == '.ir'),
                  key=lambda p: (not p.is_dir(), p.name.casefold()))


def search(root, query):
    words = query.casefold().split()
    matches = []
    for path in sorted(Path(root).rglob('*.ir')):
        relative = str(path.relative_to(root))
        if all(word in relative.casefold() for word in words):
            matches.append(path)
            if len(matches) == 200:
                break
    return matches
