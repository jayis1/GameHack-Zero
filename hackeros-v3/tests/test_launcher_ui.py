import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "staging/opt/hackeros"))
try:
    import launcher
except ImportError:
    launcher = None


@unittest.skipIf(launcher is None, "Pygame/evdev not available")
class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        font = launcher.pygame.font.Font
        def local_font(path, size):
            return font(str(Path("/usr/share/fonts/TTF") / Path(path).name) if not Path(path).exists() else path, size)
        set_mode = launcher.pygame.display.set_mode
        with patch.object(launcher, "RESULTS", Path(self.temp.name)), patch.object(launcher.threading.Thread, "start"), patch.object(launcher.pygame.font, "Font", side_effect=local_font), patch.object(launcher.pygame.display, "set_mode", side_effect=lambda *args: set_mode((640, 480))):
            self.ui = launcher.GameHackZero()
        self.ui.screen = launcher.pygame.display.set_mode((640, 480))
        self.ui.width, self.ui.height = 640, 480
        self.ui.status_line = "BAT 80%   Wi-Fi Home   12:00"

    def tearDown(self):
        launcher.pygame.quit()
        self.temp.cleanup()

    def test_all_categories_render(self):
        self.ui.home = False
        for category, (_, items) in enumerate(launcher.CATEGORIES):
            self.ui.category = category
            for index in range(len(items)):
                self.ui.item = index
                self.ui.draw()
        self.ui.category = self.ui.item = 0
        self.ui.draw()
        launcher.pygame.image.save(self.ui.screen, "/tmp/opencode/gamehack-menu-preview.png")

    def test_home_tiles_render(self):
        self.ui.home = True
        for category in range(len(launcher.CATEGORIES)):
            self.ui.category = category
            self.ui.draw()
        self.ui.category = 0
        self.ui.draw()
        launcher.pygame.image.save(self.ui.screen, "/tmp/opencode/gamehack-home-preview.png")

    def test_home_navigation_and_back(self):
        self.ui.navigate("down")
        self.assertEqual(self.ui.category, 3)
        self.ui.navigate("right")
        self.assertEqual(self.ui.category, 4)
        self.ui.navigate("confirm")
        self.assertFalse(self.ui.home)
        self.ui.navigate("down")
        self.assertEqual(self.ui.item, 1)
        self.ui.navigate("back")
        self.assertTrue(self.ui.home)

    def test_category_navigation_resets_selection(self):
        self.ui.home = False
        self.ui.item = 3
        self.ui.navigate("right")
        self.assertEqual((self.ui.category, self.ui.item), (1, 0))

    def test_rear_trigger_navigation(self):
        self.assertEqual(launcher.BUTTONS[launcher.ecodes.BTN_TL2], "back")
        self.assertEqual(launcher.BUTTONS[launcher.ecodes.BTN_TR2], "confirm")

    def test_keyboard_layout_switch_and_cancel(self):
        actions = iter(["right"] * 9 + ["down", "details", "confirm", "details", "confirm", "back"])
        self.ui.wait_action = lambda: next(actions)
        self.assertIsNone(self.ui.keyboard("Wi-Fi password", secret=True))

    def test_no_wifi_hardware_reports_error(self):
        messages = []
        self.ui.text_view = lambda title, text: messages.append((title, text))
        with patch.object(launcher, "run", return_value="usb0:ethernet:connected"):
            self.ui.wifi_setup()
        self.assertIn("No Wi-Fi interface", messages[0][1])

    def test_launcher_does_not_open_audio(self):
        self.assertIsNone(launcher.pygame.mixer.get_init())

    def test_freedoom_releases_audio_before_spawn(self):
        calls = []
        with patch.object(launcher.Path, 'is_file', return_value=True), patch.object(launcher, 'RESULTS', Path(self.temp.name)), patch.object(launcher.pygame.mixer, 'quit', side_effect=lambda: calls.append('audio released')), patch.object(launcher.subprocess, 'call', side_effect=lambda *args, **kwargs: calls.append('spawn') or 0):
            self.ui.freedoom(1)
        self.assertEqual(calls, ['audio released', 'spawn'])
