import importlib.machinery
import importlib.util
import multiprocessing
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


def load(name, relative):
    source = Path(__file__).parent / 'staging' / relative
    if not source.exists():
        source = Path('/') / relative
    loader = importlib.machinery.SourceFileLoader(name, str(source))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


worker = load('worker', 'usr/local/lib/gamehack-worker.py')
radio = load('radio', 'usr/local/sbin/gamehack-radio')


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = patch.object(worker, 'HOME', Path(self.temp.name))
        self.state = patch.object(worker, 'STATE', Path(self.temp.name) / 'state')
        self.home.start()
        self.state.start()
        (worker.HOME / 'shared').mkdir()

    def tearDown(self):
        self.home.stop()
        self.state.stop()
        self.temp.cleanup()

    def test_queue_and_validation(self):
        identifier = worker.submit('printf hello')
        self.assertEqual(worker.job_id(identifier), identifier)
        with worker.database() as db:
            self.assertEqual(db.execute('SELECT state FROM jobs').fetchone()[0], 'queued')
        for task in ('', 'x' * 2049, 'a\0b'):
            with self.assertRaises(ValueError):
                worker.submit(task)
        with self.assertRaises(ValueError):
            worker.job_id('../oops')

    def test_queue_bound(self):
        for number in range(20):
            worker.submit('true')
        with self.assertRaises(ValueError):
            worker.submit('true')

    def wait_state(self, identifier, expected):
        for attempt in range(100):
            with worker.database() as db:
                state = db.execute('SELECT state FROM jobs WHERE id=?', (identifier,)).fetchone()[0]
            if state == expected:
                return
            time.sleep(0.1)
        self.fail(f'Expected {expected}, got {state}')

    def test_daemon_executes_and_cancels(self):
        first = worker.submit('printf worker-ok')
        second = worker.submit('sleep 20')
        process = multiprocessing.get_context('fork').Process(target=worker.daemon)
        process.start()
        try:
            self.wait_state(first, 'done')
            self.assertEqual((worker.STATE / (first + '.log')).read_text(), 'worker-ok')
            self.wait_state(second, 'running')
            with worker.database() as db:
                db.execute('UPDATE jobs SET cancel=1 WHERE id=?', (second,))
            self.wait_state(second, 'cancelled')
        finally:
            process.terminate()
            process.join(timeout=5)

    def test_radio_capture_bounds(self):
        for name, freq, bssid, duration in [('a;bad', 2412, '12:34:56:78:90:ab', 10), ('wlan0', 100, '12:34:56:78:90:ab', 10), ('wlan0', 2412, 'ff:ff:ff:ff:ff:ff', 10), ('wlan0', 2412, '12:34:56:78:90:ab', 31)]:
            with self.assertRaises(ValueError):
                radio.validate_capture(name, freq, bssid, duration)

    def test_stock_radio_refuses_unsupported_monitor(self):
        with patch.object(radio, 'radios', return_value=[{'interface': 'wlan0', 'monitor_supported': False}]), patch.object(radio, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'does not advertise'):
                radio.capture('wlan0', 2412, '12:34:56:78:90:ab', 10)
            command.assert_not_called()

    def test_bluetooth_restores_power_and_discovery(self):
        def run(args, timeout=15):
            return 'Powered: no\nDiscovering: no' if args == ['bluetoothctl', 'show'] else ''
        with patch.object(radio, 'run', side_effect=run) as command, patch.object(radio, 'rfkill_states', return_value=[]), patch('builtins.print'):
            radio.main(['bluetooth-scan', '5'])
            self.assertEqual(command.call_args_list[-1].args[0], ['bluetoothctl', 'power', 'off'])
            self.assertIn(['bluetoothctl', 'scan', 'off'], [call.args[0] for call in command.call_args_list])

    def test_rfkill_restores_after_error(self):
        state = {'id': '3', 'type': 'wlan', 'name': 'phy0', 'soft': True, 'hard': False}
        with patch.object(radio, 'rfkill_states', return_value=[state]), patch.object(radio, 'run') as command:
            with self.assertRaises(RuntimeError):
                with radio.radio_available('wlan', 'phy0'):
                    raise RuntimeError('scan failed')
            self.assertEqual([call.args[0] for call in command.call_args_list], [['rfkill', 'unblock', '3'], ['rfkill', 'block', '3']])

    def test_rfkill_does_not_change_other_phy(self):
        state = {'id': '3', 'type': 'wlan', 'name': 'phy1', 'soft': True, 'hard': False}
        with patch.object(radio, 'rfkill_states', return_value=[state]), patch.object(radio, 'run') as command:
            with radio.radio_available('wlan', 'phy0'):
                pass
            command.assert_not_called()

    def test_rfkill_never_bypasses_hardware_block(self):
        state = {'id': '3', 'type': 'bluetooth', 'name': 'hci0', 'soft': True, 'hard': True}
        with patch.object(radio, 'rfkill_states', return_value=[state]), patch.object(radio, 'run') as command:
            with self.assertRaises(ValueError):
                with radio.radio_available('bluetooth'):
                    pass
            command.assert_not_called()


if __name__ == '__main__':
    unittest.main()
