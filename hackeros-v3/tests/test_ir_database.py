import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / 'staging/usr/local/lib/gamehack-zero'))
sys.path.insert(0, str(PROJECT / 'staging/opt/hackeros'))
from ir_database import buttons, load_button, waveform
from ir_library import entries, search
from tiqiaa_ir import load_signal


class IRDatabaseTests(unittest.TestCase):
    def remote(self, root):
        path = root / 'Test.ir'
        path.write_text('Filetype: IR signals file\nVersion: 1\n#\nname: Power\ntype: parsed\nprotocol: NEC\naddress: 10 00 00 00\ncommand: 20 00 00 00\n#\nname: Vol+\ntype: raw\nfrequency: 38000\nduty_cycle: 0.33\ndata: 9000 4500 560 560 560\n')
        return path

    def test_buttons_are_not_concatenated(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.remote(Path(folder))
            self.assertEqual([b['name'] for b in buttons(path)], ['Power', 'Vol+'])
            self.assertEqual(load_button(path, 1), (38000, [9000, 4500, 560, 560, 560]))
            with self.assertRaises(ValueError):
                load_signal(path)

    def test_nec_inverse_and_lsb_order(self):
        carrier, data = waveform({'type': 'parsed', 'protocol': 'NEC', 'address': '10 00 00 00', 'command': '20 00 00 00'})
        self.assertEqual(carrier, 38000)
        self.assertEqual(data[:2], [9000, 4500])
        payload = sum((1 << bit) for bit in range(32) if data[3 + bit * 2] == 1690)
        self.assertEqual(payload.to_bytes(4, 'little'), bytes([0x10, 0xef, 0x20, 0xdf]))
        self.assertEqual(len(data), 67)

    def test_necext_preserves_full_command(self):
        _, data = waveform({'type': 'parsed', 'protocol': 'NECext', 'address': '34 12 00 00', 'command': '78 56 00 00'})
        payload = sum((1 << bit) for bit in range(32) if data[3 + bit * 2] == 1690)
        self.assertEqual(payload, 0x56781234)

    def test_unsupported_and_bad_values(self):
        for item in [
            {'type': 'parsed', 'protocol': 'RC5'},
            {'type': 'parsed', 'protocol': 'NEC', 'address': '00 01 00 00', 'command': '00 00 00 00'},
            {'type': 'raw', 'frequency': '38000', 'data': '0 1'},
            {'type': 'raw', 'frequency': '0', 'data': '1 1'},
            {'type': 'raw', 'frequency': '38000', 'data': '2000000 2000000'},
        ]:
            with self.assertRaises(ValueError):
                waveform(item)

    def test_index_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.remote(Path(folder))
            for index in (-1, 2):
                with self.assertRaises(ValueError):
                    load_button(path, index)

    def test_legacy_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'capture.txt'
            path.write_text('pulse 9000\nspace 4500\npulse 560\n')
            self.assertEqual(load_signal(path), (38000, [9000, 4500, 560]))

    def test_browse_and_case_insensitive_search(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'TVs').mkdir()
            self.remote(root / 'TVs')
            (root / 'README.md').write_text('License')
            self.assertEqual([p.name for p in entries(root)], ['TVs'])
            self.assertEqual([p.name for p in search(root, 'tvs TEST')], ['Test.ir'])
