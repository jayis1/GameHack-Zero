import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "staging/opt/hackeros"))
from customization import Preferences, THEMES, load_themes, search_files


class CustomizationTests(unittest.TestCase):
    def test_preferences_round_trip(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "settings.json"
            settings = Preferences(path)
            settings.toggle_favorite("wifi")
            settings.record("wifi")
            settings.record("ir-status")
            settings.record("wifi")
            settings.theme = "Mono high contrast"
            settings.save()
            restored = Preferences(path)
            self.assertEqual(restored.favorites, ["wifi"])
            self.assertEqual(restored.recent, ["wifi", "ir-status"])
            self.assertEqual(restored.theme, "Mono high contrast")
            restored.toggle_favorite("wifi")
            self.assertEqual(Preferences(path).favorites, [])

    def test_corrupt_settings(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "settings.json"
            for text in ("{broken", "[]", '{"favorites": [{}, 5, "wifi", "wifi"]}'):
                path.write_text(text)
                settings = Preferences(path)
                self.assertEqual(settings.theme, "Momentum amber")
                self.assertTrue(all(isinstance(value, str) for value in settings.favorites))

    def test_custom_theme_validation(self):
        with tempfile.TemporaryDirectory() as root:
            pack = Path(root) / "valid"
            pack.mkdir()
            (pack / "theme.json").write_text(json.dumps({"name": "Custom", "colors": THEMES["Momentum amber"]}))
            invalid = Path(root) / "invalid"
            invalid.mkdir()
            colors = dict(THEMES["Momentum amber"], bg=[999, 0, 0])
            (invalid / "theme.json").write_text(json.dumps({"name": "Invalid", "colors": colors}))
            self.assertIn("Custom", load_themes(root))
            self.assertNotIn("Invalid", load_themes(root))

    def test_bounded_search_and_no_symlink_traversal(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            (Path(root) / "Remote.IR").write_text("test")
            (Path(outside) / "remote-secret.ir").write_text("test")
            (Path(root) / "linked").symlink_to(outside, target_is_directory=True)
            results = search_files([root], "remote")
            self.assertEqual(results, [str(Path(root) / "Remote.IR")])
            self.assertEqual(search_files([root], "remote", max_entries=1), [])


if __name__ == "__main__":
    unittest.main()
