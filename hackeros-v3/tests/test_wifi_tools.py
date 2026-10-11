import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "staging/opt/hackeros"))
from wifi_tools import parse_networks, split_fields


class WifiTests(unittest.TestCase):
    def test_escaped_ssid(self):
        self.assertEqual(split_fields(r"*:Cafe\:guest\\room:78:WPA2"),
                         ["*", "Cafe:guest\\room", "78", "WPA2"])

    def test_sort_deduplicate_and_skip_errors(self):
        networks = parse_networks(":Home:50:WPA2\n:Home:75:WPA2\n*:Other:20:WPA3\n:Open:90:\nError:No hardware\n::50:WPA2\n:Bad:NaN:WPA2")
        self.assertEqual([item["ssid"] for item in networks], ["Other", "Open", "Home"])
        self.assertEqual(networks[2]["signal"], 75)
        self.assertEqual(networks[1]["security"], "")


if __name__ == "__main__":
    unittest.main()
