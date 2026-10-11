import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "staging/opt/hackeros"))
try:
    import freedoom_runner as runner
    from freedoom_runner import axis_direction, BUTTON_KEYS, E
except ImportError:
    axis_direction = None


@unittest.skipIf(axis_direction is None, "evdev unavailable")
class FreedoomTests(unittest.TestCase):
    def test_sd2_wad_preferred_with_internal_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / 'data/external/roms/doom/freedoom1.wad'
            with patch.object(runner, 'Path', side_effect=lambda value: root / str(value).lstrip('/')):
                self.assertEqual(runner.wad_path(1), root / 'opt/freedoom/freedoom1.wad')
                external.parent.mkdir(parents=True)
                external.write_bytes(b'IWAD')
                self.assertEqual(runner.wad_path(1), external)

    def test_unsigned_stick_center(self):
        self.assertEqual(axis_direction(0, 0, 4095), -1)
        self.assertEqual(axis_direction(2048, 0, 4095), 0)
        self.assertEqual(axis_direction(4095, 0, 4095), 1)

    def test_hat(self):
        self.assertEqual([axis_direction(v, -1, 1) for v in (-1, 0, 1)], [-1, 0, 1])

    def test_controller_buttons(self):
        self.assertEqual(BUTTON_KEYS[E.BTN_EAST], E.KEY_SPACE)
        self.assertEqual(BUTTON_KEYS[E.BTN_SOUTH], E.KEY_LEFTCTRL)
        self.assertEqual(BUTTON_KEYS[E.BTN_TL2], E.KEY_ESC)
        self.assertEqual(BUTTON_KEYS[E.BTN_TR2], E.KEY_ENTER)

    def run_with_legacy_devices(self, spawn_error=False):
        # No __enter__/__exit__: reproduces the Debian evdev API on the card.
        device = SimpleNamespace(grab=Mock(), ungrab=Mock(), close=Mock())
        keyboard = SimpleNamespace(close=Mock())
        process = SimpleNamespace(poll=Mock(return_value=0), wait=Mock(return_value=0), returncode=0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wad = root / "opt/freedoom/freedoom1.wad"
            wad.parent.mkdir(parents=True)
            wad.write_bytes(b"IWAD")
            with patch.object(runner, "Path", side_effect=lambda value: root / str(value).lstrip("/")), \
                    patch.object(runner.shutil, "which", return_value="/usr/games/crispy-doom"), \
                    patch.object(runner, "controller", return_value=device), \
                    patch.object(runner, "UInput", return_value=keyboard), \
                    patch.object(runner.time, "sleep"), \
                    patch.object(runner.subprocess, "Popen", side_effect=OSError("spawn failed") if spawn_error else None, return_value=process):
                if spawn_error:
                    with self.assertRaises(OSError):
                        runner.play(1)
                else:
                    self.assertEqual(runner.play(1), 0)
        device.grab.assert_called_once()
        device.ungrab.assert_called_once()
        device.close.assert_called_once()
        keyboard.close.assert_called_once()

    def test_legacy_evdev_without_context_manager(self):
        self.run_with_legacy_devices()

    def test_spawn_failure_releases_controller(self):
        self.run_with_legacy_devices(spawn_error=True)


if __name__ == "__main__":
    unittest.main()
