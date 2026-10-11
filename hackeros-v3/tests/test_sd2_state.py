import importlib.util
import tempfile
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[1] / 'staging/usr/local/lib/gamehack-zero/sd2_state.py'
if not source.exists():
    source = Path('/usr/local/lib/gamehack-zero/sd2_state.py')
spec = importlib.util.spec_from_file_location('sd2_state', source)
state = importlib.util.module_from_spec(spec)
spec.loader.exec_module(state)


class SD2StateTests(unittest.TestCase):
    def test_decodes_clock_update_not_reset(self):
        self.assertEqual(state.clock_command(0x202000), {'clock_update': True, 'wait_previous_data': True, 'start_pending': False})
        self.assertTrue(state.clock_command(0x80202000)['start_pending'])

    def test_selects_controller_not_host_number(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, controller in [('mmc1', 'ff380000.mmc'), ('mmc0', 'ff370000.mmc')]:
                host = root / 'sys/class/mmc_host' / name
                host.mkdir(parents=True)
                target = root / 'sys/devices/platform' / controller
                target.mkdir(parents=True)
                (host / 'device').symlink_to(target)
            self.assertEqual(state.hosts(root), ['mmc1'])

    def test_absent_debugfs_is_reported_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            result = state.report(root)
            self.assertIn('Unavailable:', result)
            self.assertEqual(list(root.iterdir()), [])

    def test_reads_are_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'state'
            file.write_text('x' * (state.LIMIT + 10))
            self.assertEqual(len(state.read(file)), state.LIMIT)
