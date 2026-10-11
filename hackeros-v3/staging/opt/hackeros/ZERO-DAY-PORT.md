# Zero-Day OS to GameHack Zero feature map

Source revision: `b697bdd50d4ea38cfb421e60353ecbe42343f7f4`.

This is an inventory and port backlog, not a claim that all upstream scripts are installed.
Do not mix Kali rolling repositories into the working Debian handheld or copy Raspberry Pi boot overlays.

| Group | Feature | Status | Handheld adaptation |
|---|---|---|---|
| bluetooth | bettercap | pending port | Needs source/dependency review and a controller workflow; not installed. |
| bluetooth | ble-gatt | pending port | Needs source/dependency review and a controller workflow; not installed. |
| bluetooth | ble-spam | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| bluetooth | bt-attack | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| bluetooth | bt-deep | pending port | Needs source/dependency review and a controller workflow; not installed. |
| bluetooth | bt-scan | adapted subset | Bounded Bluetooth discovery; hardware support remains unverified. |
| camera | cam-ocr | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| camera | cam-snap | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| camera | cam-stream | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| dongle | dongle-setup | adapted subset | RTL8821CU driver and capability checks; native loading still needs testing. |
| hardware | gatt_server.py | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | c6l-ctl | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | c6l-middleman | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | cardputer-battery | adapted subset | Linux power-supply readings, not Cardputer BQ27220 registers. |
| hardware | doom-play | adapted subset | Freedoom Phase 1/2 with controller bridge and audio-contention fix. |
| hardware | ext-display | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | gpio-probe | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | gps-ctl | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | install-janos | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | jellyfin-tv | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | monsterctl | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | oled-ctl | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | retro-play | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | rf-capture | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | rfid2-ctl | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | sdr-scan | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | yt | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| hardware | zeroday-ble-remote | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| ir | ir-brute | pending port | Needs source/dependency review and a controller workflow; not installed. |
| ir | ir-replay | adapted subset | Raw IR replay with the supported USB device; native testing required. |
| ir | ir-scan | adapted subset | Tiqiaa USB raw IR learning; original Cardputer GPIO IR is not used. |
| mesh | mesh-chat | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| mesh | mesh-setup | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| network | arpspoof | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | captive-portal | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | device-classify | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | dhcp-attack | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | doh-proxy | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | exfil-discord | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | exfil-dns | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | gobuster | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | http-probe | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | install_ragnar_port.sh | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | iot-scan | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | net-discover | adapted subset | Existing authorized local-network discovery. |
| network | net-pivot | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | net-quickscan | adapted subset | Existing user-confirmed target scanning; not every upstream preset. |
| network | net-vulnscan | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | ntlmrelayx | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | quick-c2 | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | ragnar-ctl | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | ragnar-scan | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| network | snmp-scan | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | threat-intel | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | tunnel-mgr | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | vlan-hop | pending port | Needs source/dependency review and a controller workflow; not installed. |
| network | wardrive | pending port | Needs source/dependency review and a controller workflow; not installed. |
| nfc | nfc-clone | excluded | User explicitly excluded NFC and Sub-GHz. |
| nfc | nfc-emulate | excluded | User explicitly excluded NFC and Sub-GHz. |
| nfc | nfc-read | excluded | User explicitly excluded NFC and Sub-GHz. |
| reverse | hydra | pending port | Needs source/dependency review and a controller workflow; not installed. |
| reverse | john | pending port | Needs source/dependency review and a controller workflow; not installed. |
| reverse | kerberoast | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| reverse | pass-spray | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| reverse | payload-craft | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| reverse | post-harvest | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| reverse | privesc-check | pending port | Needs source/dependency review and a controller workflow; not installed. |
| reverse | revshell-stabilize | pending port | Needs source/dependency review and a controller workflow; not installed. |
| subghz | subghz-record | excluded | User explicitly excluded NFC and Sub-GHz. |
| subghz | subghz-replay | excluded | User explicitly excluded NFC and Sub-GHz. |
| subghz | subghz-scan | excluded | User explicitly excluded NFC and Sub-GHz. |
| system | cardputer-wifi-connect | adapted subset | NetworkManager controller Wi-Fi setup. |
| system | cardputer-wifi-setup | adapted subset | NetworkManager controller Wi-Fi setup. |
| system | cardputer-wifi-toggle | adapted subset | Allowlisted Wi-Fi enable action; USB faults are not bypassed. |
| system | device-lock | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | engagement-clean | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| system | first-boot | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | loot-organize | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | mac-rotate | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | opencode-ask | adapted subset | Cancelable quick-prompt client already deployed. |
| system | opencode-session | implemented frontend | Local interactive OpenCode PTY with 112px coding-keyboard dock; native OpenCode/provider execution still needs testing. |
| system | panic | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| system | power-mode | adapted subset | Existing handheld power profiles; no Pi-specific CPU hotplug copied. |
| system | stealth-backlight-toggle | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | tamper-watch | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| system | usb-gadget-mode | adapted subset | Existing host/network-role controls; not all HID/storage modes. |
| system | webui | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | webui-toggle | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | zd-boot-profile | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | zd-power | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | zeroday-boot | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| system | zeroday-bootanim | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| system | zeroday-crypt | pending port | Needs source/dependency review and a controller workflow; not installed. |
| system | zeroday-secureboot | hardware-dependent | Cardputer/Pi assumptions do not map directly to RK3326; absent sensors/radio/display hardware are not emulated. |
| system | zeroday-security-check | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wifi-autocrack | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| wifi | wifi-crack | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wifi-deauth | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| wifi | wifi-evil-twin | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| wifi | wifi-handshake | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wifi-karma-ap | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |
| wifi | wifi-monitor-toggle | adapted subset | Dedicated external-adapter passive capture; restores temporary interface. |
| wifi | wifi-pmkid | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wifi-probe-dump | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wifi-scan | adapted subset | Controller Wi-Fi scan/connect; no hardcoded wlan0. |
| wifi | wifi-survey-log | pending port | Needs source/dependency review and a controller workflow; not installed. |
| wifi | wps-attack | needs scoped review | Not auto-installed: requires target-scoped authorization, safeguards and dependency review; no blanket attack/wipe/exfiltration automation. |

## Other components

- Compositor: retain working Pygame/KMS display for now; no HDMI/ST7789/Cardputer keyboard assumptions.
- Terminal: original local PTY/controller terminal staged with a shallow coding keyboard.
- Explorer: existing browse/search are a subset; copy/move/rename/archive/hex/bookmarks remain pending.
- Trail: Wi-Fi breadcrumb storage/navigation remains pending; never imply GPS/IMU direction without hardware.
- Media/YouTube/Jellyfin/RetroArch: pending packages and controller/display/audio integration; no copyrighted ROMs.
- Security/lock/encryption: pending explicit design; no destructive panic wiping or broad root remote shell.
- Mesh/NFC/Sub-GHz/camera/MonsterC5/Grove: cannot be claimed without hardware; NFC/Sub-GHz excluded.

Inventory: 107 script files; 150 upstream menu entries.
