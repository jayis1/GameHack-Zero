# Reversible NCM diagnostic test

The original ECM/RNDIS g_ether gadget enumerates on the PC, but host cdc_ether
packet transmission times out on both a hub and direct port, including a
replacement known-good data cable. Pi logs confirm worker startup, USB IP
192.168.77.1 activation and SSH listening. This does not establish whether the
remaining cause is driver/protocol behavior, physical USB port or power.

The test uses the installed usb_f_ncm module through configfs, with a dedicated
systemd service. The standalone g_ncm module is not built in this kernel.
g_ether is removed from its two automatic load declarations, not uninstalled.
There is only one deliberate gadget setup path; no controller resets or other
gadgets are changed. Kernel, firmware, DTB and peripheral-mode overlay remain
unchanged. The new host driver is cdc_ncm rather than cdc_ether; USB identity is
0525:a4a1, a Linux NCM gadget identifier. MACs, USB subnet, no-default-route
policy and SSH pairing keys stay unchanged. This is an experimental protocol
change, NOT a demonstrated fix. MaxPower is only a USB descriptor, not a power
measurement or enforcement mechanism.

Original files, last ECM boot log and offline rollback.sh are saved under
/opt/gamehack-worker-backup/ncm-test-*/. To roll back while the Pi card is in
the PC reader, mount both partitions at /mnt/gamehack-pi and
/mnt/gamehack-pi/boot/firmware, then run the saved rollback.sh as root. It
UUID-checks the card, restores the two original files, and disables the NCM
service without deleting it or replacing any pairing identity.

Native NCM enumeration, IP transfer, SSH and task operation must be tested on
the PC before attempting the handheld again. SD2 timeout and handheld shared
USB/Wi-Fi behavior remain separate unresolved issues.

## Native PC validation — October 11, 2026

With the replacement known-good cable and direct PC USB port, the Pi enumerated
as NCM and the PC bound cdc_ncm. Pinned-host/key SSH succeeded. The worker
reported uptime 95 seconds. A queued printf task completed with exit code 0;
its saved result contained GAMEHACK_NCM_WORKER_OK. A running sleep task was
successfully cancelled. No NCM transmit-watchdog errors were seen in the
inspected test window. The existing PC NetworkManager connection subsequently
obtained 192.168.77.2 by DHCP from the Pi, with no gateway or DNS advertised;
the PC internet routes remained unchanged. Temporary test profiles were removed.

Native brcmfmac reports no Wi-Fi monitor support. Bluetooth controller is
present but soft-blocked; discovery and state restoration are not yet natively
tested. The image's first-user SSH banner is stale: authentication demonstrably
works. No kernel/firmware replacement was needed for this successful PC test.
This validates NCM on the PC, not USB/Wi-Fi coexistence on GameHack or SD2.
