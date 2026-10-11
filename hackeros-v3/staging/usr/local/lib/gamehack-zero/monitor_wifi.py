#!/usr/bin/env python3
"""Bounded, BSSID-filtered passive capture on the dedicated USB dongle."""
import argparse
import json
import os
import pwd
import re
import signal
import subprocess
import tempfile
from pathlib import Path

SUPPORTED_USB = {"0bda:c820"}
MONITOR_NAME = "ghmon0"


def command(args, timeout=15):
    result = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or f"Command failed: {args[0]}")
    return result.stdout


def adapters(sysroot=Path("/sys")):
    devices = []
    for path in sorted((sysroot / "class/net").glob("*")):
        phy = path / "phy80211"
        if not phy.exists():
            continue
        usb = ""
        device = (path / "device").resolve()
        for parent in (device, *device.parents):
            try:
                usb = (parent / "idVendor").read_text().strip().lower() + ":" + (parent / "idProduct").read_text().strip().lower()
                break
            except OSError:
                continue
        driver = (device / "driver").resolve().name if (device / "driver").exists() else "unknown"
        phyname = phy.resolve().name
        try:
            modes = command(["iw", "phy", phyname, "info"])
            monitor = bool(re.search(r"^\s*\* monitor\s*$", modes, re.M))
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            monitor = False
        devices.append({"interface": path.name, "phy": phyname, "usb": usb,
                        "driver": driver, "monitor": monitor, "supported": usb in SUPPORTED_USB})
    return devices


def validate_capture(interface, bssid, frequency, seconds):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", interface):
        raise ValueError("Invalid wireless interface")
    if not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", bssid) or int(bssid[:2], 16) & 1:
        raise ValueError("Invalid access-point BSSID")
    if not 2400 <= frequency <= 5900 or not 1 <= seconds <= 60:
        raise ValueError("Frequency or capture duration outside allowed bounds")


def disconnect(interface):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,15}", interface):
        raise ValueError("Invalid wireless interface")
    selected = next((device for device in adapters() if device["interface"] == interface), None)
    if not selected or not selected["supported"]:
        raise RuntimeError("Only the dedicated external dongle may be disconnected here.")
    return command(["nmcli", "dev", "disconnect", interface])


def output_file():
    # Create the user-owned capture as hacker, not with root filesystem access.
    account = pwd.getpwnam("hacker")
    uid, gid, groups = os.geteuid(), os.getegid(), os.getgroups()
    try:
        os.setgroups([account.pw_gid])
        os.setegid(account.pw_gid)
        os.seteuid(account.pw_uid)
        directory = Path("/data/gamehack-zero/captures")
        directory.mkdir(parents=True, exist_ok=True)
        return tempfile.mkstemp(prefix="wifi-monitor-", suffix=".pcap", dir=directory)
    finally:
        os.seteuid(uid)
        os.setegid(gid)
        os.setgroups(groups)


def capture(interface, bssid, frequency, seconds):
    validate_capture(interface, bssid, frequency, seconds)
    selected = next((device for device in adapters() if device["interface"] == interface), None)
    if not selected or not selected["supported"] or not selected["monitor"]:
        raise RuntimeError("Select the dedicated RTL8821CU USB adapter with advertised monitor support.")
    state = command(["nmcli", "-g", "GENERAL.STATE", "dev", "show", interface]).strip()
    match = re.match(r"(\d+)", state)
    if not match:
        raise RuntimeError("Cannot verify the dongle's connection state; refusing capture.")
    if 40 <= int(match[1]) <= 100:
        raise RuntimeError("The dongle is connecting/connected. Disconnect it in Wi-Fi setup first; use built-in Wi-Fi for internet.")
    if Path("/sys/class/net", MONITOR_NAME).exists():
        raise RuntimeError("ghmon0 already exists; refusing to alter an existing interface.")
    created, fd, filename = False, None, None
    try:
        command(["iw", "phy", selected["phy"], "interface", "add", MONITOR_NAME, "type", "monitor"])
        created = True
        command(["nmcli", "dev", "set", MONITOR_NAME, "managed", "no"])
        command(["ip", "link", "set", MONITOR_NAME, "up"])
        command(["iw", "dev", MONITOR_NAME, "set", "freq", str(frequency)])
        fd, filename = output_file()
        packet_filter = f"wlan addr1 {bssid} or wlan addr2 {bssid} or wlan addr3 {bssid}"
        try:
            result = subprocess.run(["tcpdump", "-Z", "hacker", "-i", MONITOR_NAME, "-U", "-s", "256", "-c", "1000",
                                     "-w", f"/proc/self/fd/{fd}", packet_filter],
                                    pass_fds=(fd,), capture_output=True, text=True, timeout=seconds)
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
        except subprocess.TimeoutExpired:
            pass
        return f"Saved: {filename}\nBSSID: {bssid}\nFrequency: {frequency} MHz\nLimit: {seconds}s / 1000 packets, 256 bytes per packet.\nNo injection or disconnect frames transmitted."
    finally:
        if fd is not None:
            os.close(fd)
        if created:
            command(["iw", "dev", MONITOR_NAME, "del"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("list")
    disc = sub.add_parser("disconnect")
    disc.add_argument("interface")
    cap = sub.add_parser("capture")
    cap.add_argument("interface")
    cap.add_argument("bssid")
    cap.add_argument("frequency", type=int)
    cap.add_argument("seconds", type=int)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise RuntimeError("Capture interrupted; restoring the adapter.")
    if args.action == "capture":
        signal.signal(signal.SIGTERM, interrupted)
        signal.signal(signal.SIGINT, interrupted)
    try:
        if args.action == "list":
            print(json.dumps(adapters()))
        elif args.action == "disconnect":
            if os.geteuid() != 0:
                raise RuntimeError("Disconnect requires the authorized system action.")
            print(disconnect(args.interface))
        else:
            if os.geteuid() != 0:
                raise RuntimeError("Capture requires the authorized system action.")
            print(capture(args.interface, args.bssid, args.frequency, args.seconds))
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"Monitor error: {exc}")
        raise SystemExit(1)
