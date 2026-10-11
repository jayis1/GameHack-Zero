# R36XX built-in Wi-Fi support

Documented R36XX Wi-Fi boards contain a Realtek RTL8188ETV USB radio:
https://handhelds.miraheze.org/wiki/R36XX
https://static.wikitide.net/handheldswiki/b/b1/R36XX_wifi_board_2.webp

The installed 6.12.32 kernel provides rtl8xxxu and RTL8188E firmware already.
The R36S base device tree disabled EHCI/OHCI host controllers ff340000 and
ff350000. Enable those controllers in all three boot-device-tree variants;
leave OTG ff300000, display overlays, regulators and GPIO assignments unchanged.

Run the root-only host tool `enable-r36xx-usb-wifi.sh MOUNTED_ROOT` when deploying
to this R36XX. It backs up the current device trees before changing them.

This is a hardware-enumeration fix, not a verified radio identification for
every R36XX revision. After reboot, QUICK > Find & connect Wi-Fi should show
networks if the radio enumerates. Otherwise inspect the kernel journal for
USB IDs, rtl8xxxu probe errors and missing firmware before choosing a driver.

No Bluetooth support is inferred from this Wi-Fi chip.

## OTG host test after unsuccessful EHCI/OHCI probe

The October 10 test boot loaded rtl8xxxu and enabled EHCI/OHCI, but no Wi-Fi
USB device enumerated. ArkOS's Panel 4 DTB leaves DWC2 in `otg` mode, unlike
the GameHack maintenance configuration that forces `peripheral` mode.
Reference: https://github.com/AeolusUX/R36S-DTB/tree/main/R36S/Panel%204

The host test forces DWC2 to `host` to check whether this board's Wi-Fi is
wired to that bus. This is an unverified wiring hypothesis, not proof that
the RTL8188ETV chip is fitted on this particular device. Boot on battery,
with the PC OTG cable disconnected. SYSTEM provides switching back to PC
network mode. If Wi-Fi still does not enumerate, inspect the actual working
ArkOS card's USB inventory and board configuration rather than guessing GPIOs.
