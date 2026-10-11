"""Offline ARM64 checks: no wireless interfaces are opened or changed."""
import ctypes
import os
import sys

sys.path.insert(0, "/opt/hackeros")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
from launcher import GameHackZero, CATEGORIES, BUTTONS, ecodes

ui = GameHackZero()
ui.draw()
ui.navigate("confirm")
for index in range(len(CATEGORIES)):
    ui.category = index
    ui.item = 0
    ui.draw()
assert BUTTONS[ecodes.BTN_TL2] == "back"
assert BUTTONS[ecodes.BTN_TR2] == "confirm"
ui.navigate("back")
assert ui.home
print("Installed home grid, categories and trigger bindings render/pass as hacker")

class BPFProgram(ctypes.Structure):
    _fields_ = [("length", ctypes.c_uint), ("instructions", ctypes.c_void_p)]

pcap = ctypes.CDLL("libpcap.so.0.8")
pcap.pcap_open_dead.argtypes = [ctypes.c_int, ctypes.c_int]
pcap.pcap_open_dead.restype = ctypes.c_void_p
pcap.pcap_compile.argtypes = [ctypes.c_void_p, ctypes.POINTER(BPFProgram), ctypes.c_char_p, ctypes.c_int, ctypes.c_uint]
pcap.pcap_freecode.argtypes = [ctypes.POINTER(BPFProgram)]
pcap.pcap_close.argtypes = [ctypes.c_void_p]
handle = pcap.pcap_open_dead(127, 65535)  # radiotap link type, no live interface
assert handle
program = BPFProgram()
try:
    expression = b"wlan addr1 12:34:56:78:90:ab or wlan addr2 12:34:56:78:90:ab or wlan addr3 12:34:56:78:90:ab"
    assert pcap.pcap_compile(handle, ctypes.byref(program), expression, 1, 0xffffffff) == 0
    pcap.pcap_freecode(ctypes.byref(program))
finally:
    pcap.pcap_close(handle)
print("Installed libpcap compiles the BSSID-only monitor filter")
