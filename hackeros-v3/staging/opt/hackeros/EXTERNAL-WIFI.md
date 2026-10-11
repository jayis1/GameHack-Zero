# External Wi-Fi monitor

CONNECT > External Wi-Fi monitor supports the plugged-in Realtek RTL8821CU
USB adapter (0bda:c820). Use a USB-C data/OTG adapter on the handheld's host
port. A powered USB hub may be needed if the dongle disconnects under load.

The 6.12.32 USB/chip modules are built from upstream Linux v6.12.32 against
this card's kernel headers and symbol versions. Existing rtw88_core, built-in
Wi-Fi, boot device trees and USB role are not replaced. Firmware is already
installed. The driver still needs an actual R36XX boot test.

The monitor screen selects the dedicated dongle, scans SSIDs/BSSIDs, selects
an access point and duration, and asks for confirmation of authorization.
Discovery uses an ordinary active Wi-Fi scan. Capture itself is passive:
no injection, deauthentication, credential cracking or automatic attacks.

Keep the external dongle disconnected from ordinary Wi-Fi connections during
monitoring. The dongle submenu offers a confirmed, dongle-only disconnect
action. Use built-in Wi-Fi for internet. Capture creates temporary ghmon0,
sets the selected AP's frequency, and filters packets by the chosen BSSID.
Maximum 60 seconds / 1000 packets / 256 captured bytes per packet. Regulatory
restrictions remain enforced by the kernel; there is no channel-limit bypass.
The temporary interface is deleted afterward, including on ordinary errors.
The original managed dongle interface and built-in connection are not changed.

PCAP files are created as hacker under /data/gamehack-zero/captures. They may
contain private network information: keep them private and delete when done.
Live monitor capture, adapter power, radio performance and packet reception
remain unverified until hardware testing.

Build reference: https://github.com/gregkh/linux/tree/v6.12.32/drivers/net/wireless/realtek/rtw88
The local build helper is prepare-rtl8821cu.py. Modules are staged in
driver-build/6.12.32-lts-rk3326. Target symbol-version CRCs and vermagic are
checked before deployment; never use these binaries on another kernel version.
