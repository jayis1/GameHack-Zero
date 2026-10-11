import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / "staging/usr/local/lib/gamehack-zero/monitor_wifi.py"
if not path.exists():
    path = Path("/usr/local/lib/gamehack-zero/monitor_wifi.py")
spec = importlib.util.spec_from_file_location("monitor_wifi", path)
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


class MonitorTests(unittest.TestCase):
    def test_disconnect_never_selects_builtin_adapter(self):
        with patch.object(monitor, "adapters", return_value=[{"interface": "wlan0", "supported": False}]), patch.object(monitor, "command") as command:
            with self.assertRaises(RuntimeError):
                monitor.disconnect("wlan0")
            command.assert_not_called()

    def test_rejects_invalid_inputs(self):
        for iface, bssid, freq, duration in (
            ("wlan1;bad", "12:34:56:78:90:ab", 2412, 15),
            ("wlan1", "not-a-bssid", 2412, 15),
            ("wlan1", "ff:ff:ff:ff:ff:ff", 2412, 15),
            ("wlan1", "12:34:56:78:90:ab", 2412, 61),
            ("wlan1", "12:34:56:78:90:ab", 123, 15),
        ):
            with self.assertRaises(ValueError):
                monitor.validate_capture(iface, bssid, freq, duration)

    def test_detects_usb_identity_and_monitor_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            net = root / "class/net/wlan1"
            usb = root / "devices/usb1/1-1"
            device = usb / "1-1:1.2"
            net.mkdir(parents=True)
            device.mkdir(parents=True)
            (usb / "idVendor").write_text("0bda\n")
            (usb / "idProduct").write_text("c820\n")
            phy = root / "class/ieee80211/phy1"
            phy.mkdir(parents=True)
            driver = root / "bus/usb/drivers/rtw88_8821cu"
            driver.mkdir(parents=True)
            (device / "driver").symlink_to(driver)
            (net / "device").symlink_to(device)
            (net / "phy80211").symlink_to(phy)
            with patch.object(monitor, "command", return_value="Supported modes:\n\t * monitor\n"):
                devices = monitor.adapters(root)
            self.assertTrue(devices[0]["supported"])
            self.assertTrue(devices[0]["monitor"])
            self.assertEqual(devices[0]["driver"], "rtw88_8821cu")

    def test_rejects_builtin_or_connected_adapter(self):
        device = {"interface": "wlan1", "supported": False, "monitor": True, "phy": "phy1"}
        with patch.object(monitor, "adapters", return_value=[device]):
            with self.assertRaises(RuntimeError):
                monitor.capture("wlan1", "12:34:56:78:90:ab", 2412, 15)
        device["supported"] = True
        with patch.object(monitor, "adapters", return_value=[device]), patch.object(monitor, "command", return_value="100 (connected)"):
            with self.assertRaises(RuntimeError):
                monitor.capture("wlan1", "12:34:56:78:90:ab", 2412, 15)

    def run_capture(self, timeout=False, failure=False):
        device = {"interface": "wlan1", "supported": True, "monitor": True, "phy": "phy1"}
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / "test.pcap"
            fd = os.open(filename, os.O_CREAT | os.O_WRONLY, 0o600)
            commands = []
            def command(args, timeout=15):
                commands.append(args)
                return "30 (disconnected)" if args[0] == "nmcli" and "GENERAL.STATE" in args else ""
            with patch.object(monitor, "adapters", return_value=[device]), \
                    patch.object(monitor, "command", side_effect=command), \
                    patch.object(monitor.Path, "exists", return_value=False), \
                    patch.object(monitor, "output_file", return_value=(fd, str(filename))), \
                    patch.object(monitor.subprocess, "run", return_value=SimpleNamespace(returncode=1 if failure else 0, stderr="failure"), side_effect=subprocess.TimeoutExpired("tcpdump", 15) if timeout else None) as run:
                if failure:
                    with self.assertRaises(RuntimeError):
                        monitor.capture("wlan1", "12:34:56:78:90:ab", 2412, 15)
                else:
                    self.assertIn("Saved:", monitor.capture("wlan1", "12:34:56:78:90:ab", 2412, 15))
                self.assertEqual(commands[-1], ["iw", "dev", "ghmon0", "del"])
                self.assertEqual(run.call_args.kwargs["timeout"], 15)
                self.assertIn("12:34:56:78:90:ab", run.call_args.args[0][-1])
                self.assertIn("1000", run.call_args.args[0])
            with self.assertRaises(OSError):
                os.fstat(fd)

    def test_capture_cleanup(self):
        self.run_capture()

    def test_capture_timeout_cleanup(self):
        self.run_capture(timeout=True)

    def test_capture_failure_cleanup(self):
        self.run_capture(failure=True)


if __name__ == "__main__":
    unittest.main()
