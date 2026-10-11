# USB-controlled worker and radios

GameHack remains the controller; the Pi waits for SSH requests and queued jobs.
USB Ethernet transports tasks/results independently of the Pi's Wi-Fi. GameHack
can retain its own Wi-Fi internet connection if the USB hardware permits both.
There is no radio passthrough: commands execute on the Pi and return over SSH.

## Commands (from GameHack's Run task on Pi keyboard)

These commands run on the Pi; they are not typed into a local GameHack shell:

    gamehack-companion submit 'uname -a'
    gamehack-companion jobs
    gamehack-companion result JOB_ID
    gamehack-companion cancel JOB_ID
    gamehack-companion radio status
    gamehack-companion radio wifi-scan wlan0
    gamehack-companion radio bluetooth-scan 10
    gamehack-companion radio bluetooth-log 10

For a radio that actually advertises monitor support, and only an AP you own
or have permission to monitor:

    gamehack-companion submit 'gamehack-companion radio wifi-capture wlan0 2412 12:34:56:78:90:ab 15'

Replace the interface, MHz frequency and BSSID with those of your permitted AP.
The dummy BSSID above is illustrative, not a discovered network. Captures are
passive, BSSID-filtered, max 30 seconds/1000 packets/128 bytes per packet. No
injection, deauthentication or cracking. Connected Pi radios are refused;
use USB for control. Temporary monitor interfaces are removed on ordinary
completion/errors. Kernel channel restrictions are not bypassed.

Pi Zero W uses built-in Broadcom brcmfmac Wi-Fi. Stock driver/firmware monitor
support is generally unavailable. Capability status is checked on the live Pi;
capture refuses unsupported hardware. No unverified Nexmon firmware/kernel
patch is installed. An external supported adapter on the Pi would require
appropriate USB host hardware: the Zero W's only data port is occupied by
device-mode USB to GameHack, so a normal hub cannot make that port both host
and gadget. Do not assume an adapter can simply plug in alongside this link.

Bluetooth discovery is active classic/LE device discovery, not Wi-Fi monitor
mode. The helper temporarily powers the Pi controller if needed and restores
its prior power state; it refuses to interrupt pre-existing discovery. btmon
observes the Pi's local controller HCI events, not arbitrary over-the-air
Bluetooth traffic. Both Bluetooth actions are bounded to 20 seconds. No
pairing, spoofing or attacks are automated.

## Queue behavior

Single worker, persistent SQLite queue, at most 20 active jobs. State/output
survive SSH disconnects. Commands execute as unprivileged companion, with
only narrow root radio/power helpers. Jobs have a 120-second runtime limit
and 256 KiB regular-file write limit; saved output max 256 KiB, displayed
preview max 12000 bytes. Cancellation stops the ordinary task process group;
privileged radio operations also have their own short time limits. Tasks can
deliberately detach; this is not an isolation/sandbox boundary. Existing queued
jobs resume after reboot; interrupted running jobs are marked interrupted.

Results: /home/companion/.local/state/gamehack-worker
Captures: /home/companion/shared/captures
Use paired-key SFTP to retrieve files. Old results need manual cleanup.

GameHack's current menu can invoke these via Run task on Pi. Dedicated queue
and radio buttons require a later 64GB-card update. This Pi-card update does
not change GameHack's Wi-Fi, USB controller wiring, or radio. Prior USB -71
disconnects cannot be fixed by installing Pi worker software.

Native Pi boot, Wi-Fi capabilities, Bluetooth and USB coexistence remain
unverified until a real hardware test.

## Radio and boot diagnostics update

The user selected Denmark (DK). The boot command line now sets the standard
cfg80211 regulatory domain, and NetworkManager's Pi Wi-Fi radio is enabled.
No network credentials or new Wi-Fi connection profiles are added. Capture
still refuses a connected or unsupported monitor radio and follows kernel
regulatory limits.

Radio actions check RF-kill state. Only the selected Wi-Fi PHY is temporarily
soft-unblocked and restored afterward, including on ordinary errors. Bluetooth
discovery temporarily unblocks its sole controller, restores its power state,
and restores any prior soft block. Multiple Bluetooth controllers require an
explicit selection workflow instead of unblocking all of them. Hardware blocks
are never bypassed. Bluetooth HCI observation does not turn on discovery.

Persistent system logs are enabled, capped at 32 MiB with seven-day retention.
No previous Pi journal was available when this update was applied. Safely shut
down the Pi before moving the card so the next boot log can be inspected.
