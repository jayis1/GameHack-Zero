"""Portable handheld customization; inspired by Momentum's UI workflows.

Original GameHack Zero implementation, not Flipper firmware or an asset decoder.
"""

import json
import os
from pathlib import Path

THEMES = {
    "Momentum amber": {
        "bg": [18, 14, 8], "panel": [37, 28, 14], "active": [67, 44, 15],
        "accent": [255, 164, 36], "focus": [255, 211, 103],
        "text": [255, 240, 211], "muted": [185, 155, 109], "error": [255, 96, 83],
    },
    "GameHack cyan": {
        "bg": [3, 10, 13], "panel": [8, 25, 29], "active": [12, 54, 57],
        "accent": [49, 232, 220], "focus": [96, 255, 155],
        "text": [225, 245, 242], "muted": [119, 156, 157], "error": [255, 99, 110],
    },
    "Mono high contrast": {
        "bg": [0, 0, 0], "panel": [16, 16, 16], "active": [55, 55, 55],
        "accent": [255, 255, 255], "focus": [255, 255, 255],
        "text": [255, 255, 255], "muted": [195, 195, 195], "error": [255, 155, 155],
    },
}


def load_themes(directory):
    themes = dict(THEMES)
    for path in sorted(Path(directory).glob("*/theme.json")):
        try:
            if path.stat().st_size > 16384:
                continue
            pack = json.loads(path.read_text())
            name = pack["name"]
            colors = pack["colors"]
            if not isinstance(name, str) or not name.strip() or len(name) > 32:
                continue
            if name in themes:
                continue
            if any(not isinstance(colors.get(key), list) or len(colors[key]) != 3
                   or any(type(value) is not int or not 0 <= value <= 255 for value in colors[key])
                   for key in THEMES["Momentum amber"]):
                continue
            themes[name] = {key: colors[key] for key in THEMES["Momentum amber"]}
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return themes


class Preferences:
    def __init__(self, path):
        self.path = Path(path)
        self.theme = "Momentum amber"
        self.favorites = []
        self.recent = []
        try:
            if self.path.stat().st_size > 16384:
                return
            data = json.loads(self.path.read_text())
            if not isinstance(data, dict):
                return
            if isinstance(data.get("theme"), str):
                self.theme = data["theme"]
            for key in ("favorites", "recent"):
                values = data.get(key, [])
                if isinstance(values, list):
                    setattr(self, key, list(dict.fromkeys(value for value in values if isinstance(value, str)))[:32])
        except (OSError, ValueError, TypeError):
            pass

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"theme": self.theme, "favorites": self.favorites, "recent": self.recent}))
        os.replace(temporary, self.path)

    def toggle_favorite(self, action):
        if action in self.favorites:
            self.favorites.remove(action)
        else:
            self.favorites = (self.favorites + [action])[-32:]
        self.save()

    def record(self, action):
        self.recent = ([action] + [value for value in self.recent if value != action])[:16]
        self.save()


def search_files(roots, query, limit=200, max_entries=10000):
    """Bounded filename search, without following directory symlinks."""
    matches = []
    visited = 0
    for root in roots:
        for directory, dirs, files in os.walk(root, followlinks=False):
            visited += 1
            if visited >= max_entries:
                return matches
            dirs[:] = sorted(name for name in dirs if not name.startswith(".")
                             and not Path(directory, name).is_symlink())
            for name in files:
                visited += 1
                if query.casefold() in name.casefold():
                    matches.append(str(Path(directory, name)))
                    if len(matches) >= limit:
                        return matches
                if visited >= max_entries:
                    return matches
    return matches
