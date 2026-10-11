# GameHack Zero 4.2.0

Consolidated development release of the updates discussed before the verified
system-card backup. This is an in-place software update, not a new flashed OS
image, a kernel upgrade, or a claim that every Zero-Day feature is ported.

## Included

- Versioned launcher, dashboard, login banner, first-use guide and splash.
- Controller navigation: L2 back/exit and R2 OK/select, including keyboards
  and Freedoom menus.
- Local PTY terminal, small flat controller keyboard and OpenCode frontend.
- Pi USB-worker client: diagnostics, pinned SSH, queue/results/cancellation.
- Pi companion release identifier 4.2.0; worker protocol remains version 2.
  Existing NCM gadget and DK regulatory settings are retained, not reinvented.
- Flipper-IRDB: 8,901 remotes, model search and individual button selection.
  Raw, NEC and NECext supported; explicit unsupported-protocol/packet limits.
- UUID-pinned GHDEBUG/GHROMS storage, safe eject, minute snapshot rotation and
  once-per-boot SD2 controller/clock/regulator diagnostics.
- Freedoom Phase 1/2 selection, SD2 WAD preference, internal fallback and
  system-card saves; audio-contention and controller integration retained.
- Existing Wi-Fi/Bluetooth/IR workflows, external RTL8821CU tools, appearance,
  favorites, recent actions and applicable Zero-Day feature inventory.
- Optional SanDisk Wireless Media Drive / Nimbus FieldKit integration:
  controller menu, local vault/snapshots, scoped connectivity checks, offline
  documents and existing Pi tools. SanDisk is NOT required by handheld/Pi tools.
  The separate project remains an independent v0.2 host prototype, not a flashed
  custom drive firmware. Stock AP/uplink had a pre-reset live test; post-reset
  status, secure custom deployment and radio auditing remain separate work.

The 256GB ROM/BIOS organization was performed separately and is not repeated
by this updater: 23 BIOS/support files moved, a Neo Geo BIOS copy added while
retaining its ROM-side dependency, and 129 empty folders prefixed X_.

## Not claimed fixed

- TF2 still fails initialization at ff380000 before partitions enumerate.
  Two new boots confirm the clock-update timeout; ROM folder/mount changes
  cannot fix this. Shared regulator voltages are not changed.
- Pi NCM worked on the PC; handheld connectivity and Wi-Fi coexistence need
  native testing. Pi stock monitor mode remains unverified.
- Native IR transmission and OpenCode provider/dialog compatibility need
  on-device testing. Tiqiaa uses a fixed ~36.6kHz carrier.
- No NFC, Sub-GHz, unverified Nexmon firmware, overclock or copied vendor DTB.

## Preservation and installation

The pre-4.2.0 whole-card image is verified and is never rewritten by the update.
It includes the already-installed IR update. The release installer requires
the correct system-card UUID, verifies every source file and backs up replaced
files. It leaves the kernel, DTB, boot.ini, cmdline, keys, networking profiles,
accounts, saved results, projects, credentials and game saves alone.
It only refreshes code/docs, known SD2 units, release identifiers and the bitmap
splash; existing system dependencies must already be installed.

The Pi release marker has a separate guarded installer. Do not apply handheld
files to the Pi or replace Raspberry Pi OS's /etc/os-release. NCM's existing
offline rollback remains available on the Pi.

After deployment: validate installed code, unmount, run read-only filesystem
checks and safely eject. Do not describe a staged release as deployed until
the actual card has been updated and verified.
