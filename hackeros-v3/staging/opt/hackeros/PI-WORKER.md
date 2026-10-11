# Pi worker

CONNECT > Raspberry Pi worker makes GameHack the controller and the Pi Zero W
an on-demand worker. Key-pinned SSH requests provide status, shared-file listing,
task commands, reboot and shutdown. No desktop or unauthenticated HTTP API.

The paired private key is in /home/hacker/.ssh/gamehack-pi/id_ed25519 (0600).
The Pi has only its public key. Host identity checking is mandatory. All normal
tasks run as companion on the Pi; only shutdown/reboot have narrow sudo access.
Task commands use the controller keyboard. Connection/task timeout is 35s,
output preview is 12000 bytes. A disconnected/timed-out task may continue on
the Pi; this is not yet a persistent job queue or cancellation protocol.

GameHack must stay in USB host mode, while the Pi runs g_ether device mode.
The worker profile matches only the paired USB Ethernet MAC address. The local
link is 192.168.77.2 -> 192.168.77.1 and never becomes the internet route.
Existing Wi-Fi connection profiles and boot/display device trees are unchanged.

Observed boot: Wi-Fi RTL8188EU 0bda:0179 on DWC2 USB 1-1 connected, then USB
disconnected with repeated protocol error -71. No Pi USB Ethernet enumerated.
This indicates USB-level failure, not a routing conflict. Logs cannot establish
whether the Wi-Fi radio is physically internal, external, or shares connector
wiring. A simple USB-A/C converter cannot multiplex devices. A proper powered
hub can support separate USB devices, but cannot fix parallel internal wiring.
Use a non-backfeeding hub and appropriate power; don't improvise dual supplies.
If internal radio/port wiring conflicts, a Wi-Fi link to the Pi is an alternative
requiring a separate Pi network/SSH configuration update.

The Pi worker requires hardware testing. Software settings cannot guarantee
simultaneous Wi-Fi/Pi operation while USB enumeration is failing.

CONNECT > Raspberry Pi worker > USB link diagnostics checks the paired host
MAC (02:47:48:50:49:02) and its NetworkManager/IPv4 state. SSH requests are
refused if that USB interface is absent rather than falling back through Wi-Fi.
The most recent connection outcome is saved privately (0600) at
/data/gamehack-zero/pi-last-connection.json. User task commands, output and
credentials are not stored in this report. Authentication, host-key and
connection-refused errors have separate explanations; host-key checking stays on.
