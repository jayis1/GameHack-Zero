GameHack Zero 4.2.0
==================
Independent controller-operated Linux toolbox for the R36XX handheld.
This is not Flipper firmware or an official Flipper Devices product.
NFC and Sub-GHz are excluded.

CONTROLS
--------
D-pad / left stick: navigate; A: confirm; B: cancel.
L2: back / exit; R2: OK / select, including keyboards and game menus.
L1 / R1: category; X: dashboard; Y: help / favorites where indicated.

LOCAL CODING
------------
DEVELOP > OpenCode / local coding TUI provides an interactive local terminal
and a small flat controller keyboard. SSH is not required to use it.
OpenCode runs as hacker, not root. Projects: /data/gamehack-zero/projects.
Cloud AI requires internet and provider credentials; native provider execution
and terminal/dialog compatibility still need on-device verification.

PI COMPANION
------------
Keep the handheld USB-C OTG port in HOST mode. Attach the Pi through the
USB-A converter and the Pi's USB/DATA port, not its power-only port.
Pi NCM USB Ethernet: Pi 192.168.77.1, handheld 192.168.77.2.
Pinned key-only SSH, bounded task queue, saved results and cancellation.
No default gateway/DNS is advertised by the Pi.
NCM works on the PC; handheld link and Wi-Fi coexistence remain unverified.
Do not use the old 10.55.0.x gadget instructions for this host-role build.

INFRARED
--------
INFRARED > Browse remote library: category/brand/model, search, then button.
8,901 remotes from Lucaslhm/Flipper-IRDB are stored on the system card.
Raw, NEC and NECext supported; other parsed protocols marked unsupported.
Tiqiaa Tview 10c4:8468 is required by the direct USB sender.
It has a fixed ~36.6kHz carrier; some database signals may not work.
Transmission needs native testing. Only operate authorized devices.
Learned remotes: /data/gamehack-zero/ir.

FREEDOOM
--------
PLAY > Freedoom Phase 1 / Phase 2 uses Crispy Doom.
D-pad moves/turns; A use; B fire; X map; Y weapon; L1/R1 strafe.
L2 back/menu; R2 confirm; L2+R2 or START+SELECT exits.
Prefer SD2 WADs if available, with internal fallback.
Saves: /data/gamehack-zero/freedoom on the system card.

EXPANSION STORAGE
-----------------
The prepared 256GB card has GHDEBUG (32GiB ext4) and GHROMS (exFAT).
Exact UUID mounts: /data/debug and /data/external.
ROMs: /data/external/roms; BIOS: /data/external/bios.
Empty folders on GHROMS were prefixed X_; a change manifest is on that card.
Absent cards do not block boot; debug reports do not spill onto root.
Minute snapshots are bounded/private; controller-state diagnostics also go
to the system-card journal after boot, even if TF2 cannot mount.
IMPORTANT: TF2 currently times out before block-device detection.
This release does not claim that the slot or ROM visibility is fixed.

NETWORKING AND SAFETY
--------------------
CONNECT > SanDisk / optional field node opens Nimbus FieldKit tools.
The SanDisk Wireless Media Drive is optional for networking and extra storage.
Local vault snapshots, scoped service checks and offline notes are available.
Custom SanDisk firmware is not installed; do not assume monitor mode, secure
administration or post-reset Internet forwarding. The Pi stays independent.
Wi-Fi, Bluetooth and external-adapter workflows depend on actual hardware.
RTL8821CU monitoring is bounded and limited to authorized networks.
Pi onboard monitor support is not confirmed; no Nexmon patch is installed.
Use the menu to shut down cleanly and safely eject both expansion partitions.
Preserve pairing identities. Never publish backups, keys or provider tokens.

Release notes: /opt/hackeros/RELEASE-4.2.0.md.
Kernel, working display DTB and USB host role are preserved by this update.
