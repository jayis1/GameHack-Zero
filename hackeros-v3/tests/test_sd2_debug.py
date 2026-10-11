import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / 'staging/usr/local/lib/gamehack-zero/sd2_debug.py'
if not source.exists():
    source = Path('/usr/local/lib/gamehack-zero/sd2_debug.py')
spec = importlib.util.spec_from_file_location('sd2_debug', source)
debug = importlib.util.module_from_spec(spec)
spec.loader.exec_module(debug)


class SD2Tests(unittest.TestCase):
    def test_accepts_only_prepared_debug_partitions(self):
        for uuid, expected in [(debug.DEBUG_UUID, True),
                               ('83809ff4-9ea9-46b0-bec0-14b719a09e61', True),
                               ('2ac15f87-aa0e-4fa6-9437-b542636d070c', False),
                               ('', False)]:
            with patch.object(debug, 'command', return_value=uuid + '\nexit=0\n'):
                self.assertEqual(debug.mounted(Path('/data/debug')), expected)

    def test_snapshot_collects_only_fixed_reports(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(debug, 'mounted', return_value=True), \
                patch.object(Path, 'read_text', return_value='00000000-0000-0000-0000-000000000001'), \
                patch.object(debug, 'command', return_value='diagnostic output\n') as command:
            self.assertTrue(debug.collect(Path(folder)))
            files = list((Path(folder) / 'sessions').glob('*/*'))
            self.assertTrue({'kernel.txt', 'network.txt', 'hardware.txt', 'services.txt'} <= {p.name for p in files})
            self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in files))
            self.assertFalse(any('pi_worker.py' in str(call) or 'capture' in str(call) for call in command.call_args_list))

    def test_absent_card_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(debug, 'mounted', return_value=False):
            root = Path(folder)
            self.assertFalse(debug.collect(root))
            self.assertEqual(list(root.iterdir()), [])

    def test_private_bounded_atomic_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'kernel.txt'
            debug.write(path, 'x' * (debug.LIMIT + 100))
            self.assertEqual(path.stat().st_size, debug.LIMIT)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'target').write_text('untouched')
            (root / 'kernel.txt').symlink_to(root / 'target')
            with self.assertRaises(ValueError):
                debug.write(root / 'kernel.txt', 'replacement')
            self.assertEqual((root / 'target').read_text(), 'untouched')

    def test_retention_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            current = root / 'boot-00000000-0000-0000-0000-000000000000'
            current.mkdir()
            for index in range(1, 25):
                path = root / f'boot-00000000-0000-0000-0000-{index:012x}'
                path.mkdir()
                (path / 'kernel.txt').write_text('snapshot')
            user = root / 'my-debug-data'
            user.mkdir()
            (user / 'notes.txt').write_text('keep me')
            debug.prune(root, current)
            self.assertEqual(len(list(root.glob('boot-*'))), debug.KEEP)
            self.assertEqual((user / 'notes.txt').read_text(), 'keep me')


if __name__ == '__main__':
    unittest.main()
