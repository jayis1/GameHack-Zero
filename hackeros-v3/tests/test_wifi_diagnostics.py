import importlib.util
import unittest
from pathlib import Path

source = Path(__file__).resolve().parents[1] / 'staging/usr/local/lib/gamehack-zero/wifi_diagnostics.py'
if not source.exists():
    source = Path('/usr/local/lib/gamehack-zero/wifi_diagnostics.py')
spec = importlib.util.spec_from_file_location('wifi_diagnostics', source)
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)


class DiagnosticsTests(unittest.TestCase):
    def test_usb_failure_is_not_missing_driver(self):
        result = diagnostics.diagnosis('lo:loopback:connected', 'device descriptor read/64, error -71')
        self.assertIn('USB enumeration failed', result)
        self.assertIn('not proof of a missing', result)

    def test_existing_interface_takes_precedence_over_old_failure(self):
        result = diagnostics.diagnosis('wlan0:wifi:disconnected', 'error -71')
        self.assertIn('detects a Wi-Fi interface', result)


if __name__ == '__main__':
    unittest.main()
