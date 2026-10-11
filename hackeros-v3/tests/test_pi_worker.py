import importlib.util
import shlex
import json
import tempfile
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[1] / 'staging/opt/hackeros/pi_worker.py'
if not source.exists():
    source = Path('/opt/hackeros/pi_worker.py')
spec = importlib.util.spec_from_file_location('pi_worker', source)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class PiWorkerTests(unittest.TestCase):
    def test_identifies_paired_usb_mac_not_wifi(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, address in [('wlan0', '00:11:22:33:44:55'), ('enx024748504902', '02:47:48:50:49:02')]:
                (root / name).mkdir()
                (root / name / 'address').write_text(address)
            self.assertEqual(worker.usb_links(root), ['enx024748504902'])

    def test_connection_diagnostics_are_private_and_do_not_include_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            worker.save_diagnostic('task', 255, 'Connection refused', [], Path(folder))
            path = Path(folder) / 'pi-last-connection.json'
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            data = json.loads(path.read_text())
            self.assertNotIn('command', data)
            self.assertNotIn('output', data)

    def test_distinguishes_ssh_error_types(self):
        self.assertIn('authentication', worker.error_reason('Permission denied (publickey).'))
        self.assertIn('identity', worker.error_reason('Host key verification failed.'))
        self.assertIn('refused', worker.error_reason('Connection refused'))

    def test_pinned_key_only_connection(self):
        args = worker.ssh_args('status')
        self.assertIn('StrictHostKeyChecking=yes', args)
        self.assertIn('BatchMode=yes', args)
        self.assertIn('IdentitiesOnly=yes', args)
        self.assertEqual(args[-2], 'companion@192.168.77.1')
        self.assertEqual(shlex.split(args[-1]), ['gamehack-companion', 'status'])

    def test_task_is_single_shell_argument(self):
        task = 'printf "%s" "hello world"; uname -a'
        self.assertEqual(shlex.split(worker.ssh_args('task', task)[-1]), ['sh', '-lc', task])

    def test_rejects_invalid_actions_and_tasks(self):
        with self.assertRaises(ValueError):
            worker.ssh_args('unknown')
        for task in ('', 'a' * 2049, 'abc\0def'):
            with self.assertRaises(ValueError):
                worker.ssh_args('task', task)


if __name__ == '__main__':
    unittest.main()
