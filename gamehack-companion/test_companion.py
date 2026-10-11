import importlib.machinery
import importlib.util
import unittest
from unittest.mock import patch
from pathlib import Path

path = Path(__file__).parent / 'staging/usr/local/bin/gamehack-companion'
if not path.exists():
    path = Path('/usr/local/bin/gamehack-companion')
loader = importlib.machinery.SourceFileLoader('companion', str(path))
spec = importlib.util.spec_from_loader(loader.name, loader)
companion = importlib.util.module_from_spec(spec)
loader.exec_module(companion)


class CompanionTests(unittest.TestCase):
    def test_status(self):
        with patch.object(companion.sys, 'argv', ['gamehack-companion', 'status']), patch('builtins.print') as output, patch.object(companion, 'status', return_value={'name': 'GameHack Companion'}):
            self.assertEqual(companion.main(), 0)
            self.assertIn('GameHack Companion', output.call_args.args[0])

    def test_power_allowlist(self):
        for action in ('shutdown', 'reboot'):
            with patch.object(companion.sys, 'argv', ['gamehack-companion', action]), patch.object(companion.subprocess, 'run') as run:
                self.assertEqual(companion.main(), 0)
                run.assert_called_once_with(['sudo', '-n', '/usr/local/sbin/gamehack-companion-power', action], check=True)

    def test_reject_extra_or_unknown_arguments(self):
        for args in (['shutdown', 'extra'], ['anything'], ['reboot;bad'], []):
            with patch.object(companion.sys, 'argv', ['gamehack-companion'] + args), patch.object(companion.subprocess, 'run') as run, patch('builtins.print'):
                self.assertEqual(companion.main(), 2)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
