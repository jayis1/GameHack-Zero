#!/usr/bin/env python3
"""GameHack Zero driver for the Tiqiaa Tview USB IR transceiver (10c4:8468)."""

import argparse
import ctypes
import ctypes.util
import math
import re
import sys
from pathlib import Path
from ir_database import buttons, load_button

VID = 0x10C4
PID = 0x8468
EP_OUT = 0x01
EP_IN = 0x81
MAX_FRAGMENT = 56


class UsbError(RuntimeError):
    pass


class Tiqiaa:
    def __init__(self):
        library = ctypes.util.find_library("usb-1.0")
        if not library:
            raise UsbError("libusb-1.0 is not installed")
        self.usb = ctypes.CDLL(library)
        self.context = ctypes.c_void_p()
        self.handle = ctypes.c_void_p()
        self.packet_id = 0
        self.command_id = 0
        self._declare_api()

    def _declare_api(self):
        self.usb.libusb_init.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
        self.usb.libusb_init.restype = ctypes.c_int
        self.usb.libusb_open_device_with_vid_pid.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_uint16]
        self.usb.libusb_open_device_with_vid_pid.restype = ctypes.c_void_p
        self.usb.libusb_set_auto_detach_kernel_driver.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.usb.libusb_claim_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.usb.libusb_claim_interface.restype = ctypes.c_int
        self.usb.libusb_release_interface.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.usb.libusb_bulk_transfer.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_uint]
        self.usb.libusb_bulk_transfer.restype = ctypes.c_int
        self.usb.libusb_close.argtypes = [ctypes.c_void_p]
        self.usb.libusb_exit.argtypes = [ctypes.c_void_p]

    def open(self):
        result = self.usb.libusb_init(ctypes.byref(self.context))
        if result:
            raise UsbError(f"libusb initialization failed ({result})")
        self.handle = self.usb.libusb_open_device_with_vid_pid(self.context, VID, PID)
        if not self.handle:
            raise UsbError("Tiqiaa Tview 10c4:8468 not found; use USB host mode")
        self.usb.libusb_set_auto_detach_kernel_driver(self.handle, 1)
        result = self.usb.libusb_claim_interface(self.handle, 0)
        if result:
            raise UsbError(f"cannot claim Tiqiaa interface ({result})")
        return self

    def close(self):
        if self.handle:
            try:
                self.command(b"L", timeout=1000)
            except Exception:
                pass
            self.usb.libusb_release_interface(self.handle, 0)
            self.usb.libusb_close(self.handle)
            self.handle = ctypes.c_void_p()
        if self.context:
            self.usb.libusb_exit(self.context)
            self.context = ctypes.c_void_p()

    def __enter__(self):
        return self.open()

    def __exit__(self, *_):
        self.close()

    def _bulk(self, endpoint, data=None, size=64, timeout=1500):
        transferred = ctypes.c_int()
        if data is None:
            buffer = (ctypes.c_ubyte * size)()
            length = size
        else:
            length = len(data)
            buffer = (ctypes.c_ubyte * length).from_buffer_copy(data)
        result = self.usb.libusb_bulk_transfer(
            self.handle, endpoint, buffer, length, ctypes.byref(transferred), timeout)
        if result:
            raise UsbError(f"USB transfer failed ({result})")
        return bytes(buffer[:transferred.value])

    def _send_packet(self, payload):
        packet = b"ST" + payload + b"EN"
        if len(packet) > 1024:
            raise ValueError("IR signal is too long for one Tiqiaa packet")
        self.packet_id = self.packet_id % 15 + 1
        count = math.ceil(len(packet) / MAX_FRAGMENT)
        for index in range(count):
            fragment = packet[index * MAX_FRAGMENT:(index + 1) * MAX_FRAGMENT]
            header = bytes((2, len(fragment) + 3, self.packet_id, count, index + 1))
            self._bulk(EP_OUT, header + fragment)

    def _read_packet(self, timeout=1500):
        packet = bytearray()
        expected = None
        while expected is None or index < expected:
            fragment = self._bulk(EP_IN, size=64, timeout=timeout)
            if len(fragment) < 5 or fragment[0] != 1:
                raise UsbError("invalid response from Tiqiaa adapter")
            expected, index = fragment[3], fragment[4]
            data_length = max(0, fragment[1] - 3)
            packet.extend(fragment[5:5 + data_length])
        if not packet.startswith(b"ST") or not packet.endswith(b"EN"):
            raise UsbError("malformed response from Tiqiaa adapter")
        return bytes(packet[2:-2])

    def command(self, command, data=b"", expect_reply=True, timeout=1500):
        self.command_id = self.command_id % 0x7F + 1
        self._send_packet(bytes((self.command_id,)) + command + data)
        return self._read_packet(timeout) if expect_reply else b""

    def version(self):
        response = self.command(b"V")
        return response

    def send(self, durations, carrier=38000):
        del carrier  # The adapter hardware uses its fixed ~36.6 kHz carrier.
        encoded = bytearray()
        pulse = True
        for duration in durations:
            ticks = max(1, round(abs(duration) / 16))
            while ticks:
                chunk = min(127, ticks)
                encoded.append((0x80 if pulse else 0) | chunk)
                ticks -= chunk
            pulse = not pulse
        self.command(b"S")
        response = self.command(b"D", b"\x00" + encoded)
        self.command(b"L")
        return response

    def receive(self, timeout=30):
        self.command(b"R")
        try:
            response = self.command(b"O", timeout=timeout * 1000)
        finally:
            try:
                self.command(b"C")
            except UsbError:
                pass
            try:
                self.command(b"L")
            except UsbError:
                pass
        if len(response) < 4 or response[1:2] != b"D":
            raise UsbError("adapter returned no captured IR signal")
        encoded = response[2:-1]
        durations = []
        previous = None
        for value in encoded:
            pulse = bool(value & 0x80)
            duration = (value & 0x7F) * 16
            if duration == 0:
                continue
            if pulse == previous:
                durations[-1] += duration
            else:
                durations.append(duration)
                previous = pulse
        if not durations:
            raise UsbError("captured IR signal was empty")
        return durations


def load_signal(filename, button=None):
    if button is not None:
        return load_button(filename, button)
    entries = buttons(filename)
    if entries:
        if len(entries) != 1:
            raise ValueError('Multi-button remote: select a button in the IR library')
        return load_button(filename, 0)
    text = Path(filename).read_text(errors="strict")
    carrier_match = re.search(r"(?im)^frequency:\s*(\d+)", text)
    carrier = int(carrier_match.group(1)) if carrier_match else 38000
    data_match = re.search(r"(?im)^data:\s*([\d\s]+)$", text)
    if data_match:  # Flipper raw .ir format; values alternate pulse/space.
        durations = [int(value) for value in data_match.group(1).split()]
    elif re.search(r"(?im)^(pulse|space)\s+\d+", text):
        durations = [int(value) for _, value in re.findall(r"(?im)^(pulse|space)\s+(\d+)", text)]
    else:  # GameHack format: one line of signed or unsigned microsecond values.
        line = next((line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")), "")
        durations = [abs(int(value)) for value in line.split()]
    if not durations or len(durations) > 4096 or any(value < 1 or value > 2_000_000 for value in durations):
        raise ValueError("invalid or unsupported IR signal file")
    return carrier, durations


def main():
    parser = argparse.ArgumentParser(description="GameHack Zero Tiqiaa USB IR driver")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    send = sub.add_parser("send")
    send.add_argument("file")
    send.add_argument('--button', type=int)
    learn = sub.add_parser("learn")
    learn.add_argument("file")
    learn.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    try:
        if args.action == 'send':
            carrier, durations = load_signal(args.file, args.button)
        with Tiqiaa() as adapter:
            if args.action == "status":
                response = adapter.version()
                print("Tiqiaa Tview 10c4:8468 connected")
                print("USB bulk protocol ready")
                print("Capabilities: transmit; short-range receive hardware present")
                print("Version response:", response.hex(" "))
            elif args.action == "send":
                adapter.send(durations, carrier)
                print(f"Transmitted {len(durations)} pulse/space durations from {args.file}")
                print(f'Requested carrier {carrier} Hz; adapter uses fixed ~36.6 kHz.')
            else:
                durations = adapter.receive(max(1, min(args.timeout, 60)))
                target = Path(args.file)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(
                    "Filetype: IR signals file\nVersion: 1\n#\nname: Captured\n"
                    "type: raw\nfrequency: 36640\nduty_cycle: 0.33\ndata: "
                    + " ".join(str(value) for value in durations) + "\n"
                )
                print(f"Captured {len(durations)} pulse/space durations to {target}")
    except (OSError, ValueError, KeyError, UsbError) as error:
        print(f"IR error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
