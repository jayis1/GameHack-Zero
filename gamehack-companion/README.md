# GameHack Companion

Customized Raspberry Pi OS Lite 32-bit for a Raspberry Pi Zero W. The
underlying distribution remains Raspberry Pi OS/Raspbian, not a new kernel.

## Connection

Insert this 32GB card into the Pi. Connect its micro-USB **USB/data** port
(not PWR IN) to the handheld's USB-C **host/OTG** port using a data cable.
Allow about 1–2 minutes for the first boot. The Pi is 192.168.77.1; its
DHCP server offers 192.168.77.2–10 to the GameHack. It does not advertise
an internet gateway, so existing handheld Wi-Fi can stay in use.

For the Pi and Wi-Fi dongle together, use an appropriately powered USB hub
that does not backfeed the handheld. Avoid improvised dual-power wiring.
If the Pi resets/disconnects, check cable quality and USB power first.

## Access and controls

SSH is key-only as `companion`, listening only on the USB address. A new
dedicated private key is held in `access/` on this PC; it is not on the Pi.
The Pi's public host key is pinned in `access/known_hosts`.

Use `./companion-ssh status`, `./companion-ssh files`,
`./companion-ssh shell`, `./companion-ssh shutdown`, or `./companion-ssh reboot`
once attached to a Linux USB host. `./companion-ssh upload LOCALFILE` transfers
a file into `/home/companion/shared/`. Downloads can use SFTP with the same
key and pinned host identity. Treat the private key as a password.

Only shutdown/reboot have narrow passwordless sudo permissions. Ordinary
SSH commands execute unprivileged. No Wi-Fi passwords, provider credentials,
attack service, public API, or internet sharing is configured.

The handheld still needs its companion client/menu installed. Repair its
reported black screen first, then transfer the dedicated key and pinned host
key to the hacker account. Never disable SSH host-key checking to pair.

The official image checksum and raw write/read-back were verified. Offline
ARM tests do not prove Pi boot or USB power/connectivity: test on hardware.

## Enhanced worker

See WORKER-RADIOS.md for the persistent job queue, cancellation, saved results,
Bluetooth discovery/local HCI observation, and capability-checked passive
Wi-Fi capture. Built-in Zero W monitor mode is not claimed or force-enabled.
