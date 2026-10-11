# 🐬 GameHack Zero

### The “Flipper 1” dev version that never was… until it sort of was.

**A Linux handheld, a tiny Pi sidekick, and a suspicious amount of ambition.**

**Consolidated development release: GameHack Zero 4.2.0.**
See [release notes](hackeros-v3/staging/opt/hackeros/RELEASE-4.2.0.md) and the
[deployment checklist](RELEASE-4.2.0.md).
Installed and verified on the handheld system card; Pi release-marker
deployment remains pending. Native hardware validation is tracked below.

> **Fictional origin story. Real DIY project.**
> GameHack Zero is an independent project—not a Flipper Devices product,
> leaked prototype, official successor, or Flipper firmware port.

---

## 📼 The prototype nobody ordered

Somewhere in an imaginary development lab, someone wrote three words on a
whiteboard:

**“What if… Doom?”**

Underneath that appeared a longer wish list: a proper screen, game controls,
Linux tools, infrared remotes, local coding, and a tiny assistant computer
that could do the boring jobs while the handheld did the interesting ones.

The folder was named `flipper_1_dev_FINAL_final_really_final`.

The prototype never shipped. Mostly because, in this story, it never existed.
There was no secret dolphin council. No forgotten factory run. No mysterious
engineering sample hiding beneath a desk.

But ideas are terrible at staying imaginary.

An R36XX handheld turned up. A Raspberry Pi Zero W volunteered for sidekick
duty. Some microSD cards joined the expedition. A controller-friendly launcher
started taking shape, and suddenly the nonexistent dev kit had a boot screen.

It wasn't a Flipper 1.

It was **GameHack Zero**: the slightly chaotic cousin from the timeline where
the pocket gadget grew game controls, learned Linux, and brought a Pi friend.

The dolphin remained fictional. The debugging did not.

## 🎮 Meet the crew

| Crew member | Job description |
| --- | --- |
| **GameHack Zero 4.2.0** | R36XX handheld running a Debian/Armbian-based system and controller-driven tools. |
| **Pi companion OS** | Raspberry Pi Zero W running Raspberry Pi OS Lite and a subordinate USB worker. |
| **USB-C IR accessory** | External infrared adapter; the sender implementation targets Tiqiaa/Tview hardware with USB ID `10c4:8468`. |
| **64GB system card** | Preserved working installation and source for the single-card migration. |
| **32GB Pi card** | The sidekick's OS, worker queue, and saved results. |
| **256GB single-card route** | BOOT, system, debug/captures and ROMs together in TF1; restoration/filesystem checks passed, native boot pending. |
| **128GB expansion card** | Prepared ROM/debug storage for TF2; native TF2 detection remains unresolved. |

The handheld is the captain. The Pi is the crew—not a replacement for the
handheld's Wi-Fi, and not an excuse to require SSH for every interaction.

## 💾 256GB single-card route — TF1 only

The current development route puts the handheld OS and libraries on **one 256GB
card in TF1**, leaving TF2 empty. This bypasses the TF2 initialization failure;
**it does not fix TF2**. The original 64GB system card remains unchanged.

| Area | Allocation | Purpose |
| --- | --- | --- |
| Reserved bootloader area | 16MiB | Preserve the working Rockchip bootloader placement |
| BOOT | 256MiB, FAT32 | Boot settings and working display/panel assets |
| System | 24GiB, ext4 | GameHack OS, apps, local state and saves |
| Debug / captures | ~27.74GiB, ext4 | Private diagnostics, authorized Wi-Fi PCAPs and recon files |
| ROMs / BIOS / media | ~186.3GiB, exFAT | Game and media library |

**20GiB was reassigned from the previous ROM allocation to debug/capture storage.**
This is shared space on the debug filesystem, not a separate enforced capture
quota. Keep captures private and only collect traffic you are permitted to inspect.

The intended mount paths remain `/data/debug` and `/data/external`; captures use
`/data/debug/captures`. Reviewed safety changes refuse capture when that debug
volume is not mounted, and refuse expansion eject when storage shares the running
system disk. **Shut down fully before removing the TF1 system card.**

**Current status:** the current system/BOOT/bootloader copy and existing ROM/BIOS
files were preserved and verified on the development PC. All 7,220 library files
passed byte-for-byte restoration verification, all four filesystems passed checks,
and bootloader/boot settings and reviewed safety updates were verified. The card
was safely ejected. Native TF1-only boot and actual ROM gameplay remain pending.
Do not treat this README as a completed
hardware test or an instruction to flash an older release image.

The draft image assets and public source snapshot do **not** yet contain a newly
validated 256GB build. No updated flashable image is being announced here. A
migration must preserve ROM/BIOS data before recreation—exFAT cannot safely shrink
in place. A single reader can be used sequentially via verified PC-held copies.

## 🧰 What's in the toolbox?

- **Controller-first launcher:** menus, on-screen keyboard, themes, favorites,
  and recent actions. **L2 goes back. R2 says yes.**
- **Networking workflows:** Wi-Fi setup, Bluetooth tools, SSH, and diagnostics.
- **USB Pi worker:** pinned, key-only SSH over a USB Ethernet link, with queued
  jobs, saved results, and cancellation.
- **Infrared library:** 8,901 remote files from
  [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB), adapted for GameHack's
  remote-and-button selection UI.
- **Local coding frontend:** an on-device terminal, controller keyboard, and
  OpenCode integration. Cloud providers still need internet and credentials.
- **Freedoom:** because every serious development story eventually becomes
  “yes, but can it run Doom?”
- **Expansion storage:** UUID-pinned debug/ROM mounts, bounded diagnostic
  snapshots, and safe-eject helpers.

**No NFC. No Sub-GHz. No pretending software can summon missing hardware.**
IR requires a supported USB adapter; other accessories have their own hardware
and driver requirements.

### USB-C infrared device

GameHack uses an **external USB-C IR adapter**, not an infrared transmitter built
into the handheld. The current sender targets **Tiqiaa/Tview (`10c4:8468`)**.
Connect it through a USB-host-capable connection (with an appropriate OTG adapter
if needed); a USB-C connector alone does not guarantee a compatible protocol.
Generic phone IR accessories are not automatically supported.

Use **INFRARED → IR hardware** to check detection, then **Browse remote library**
to select a remote and button. **R2 selects; L2 goes back.** Transmission requires
confirmation and is only for devices you own or are permitted to operate.

The adapter's sender uses a fixed **~36.6kHz carrier**. Supported database formats
are raw timings, NEC and NECext; unsupported protocols/carriers may not work.
Native capture and transmission still require hardware validation—installed
software and a populated remote library are not proof of successful IR operation.
See [IR-DATABASE.md](hackeros-v3/IR-DATABASE.md) for details.

### Optional side project — Nimbus FieldKit

The **SanDisk Wireless Media Drive / Nimbus FieldKit** project is now available
in its own public repository:
**[jayis1/nimbus-fieldkit](https://github.com/jayis1/nimbus-fieldkit)**.

It provides the optional networking/storage/field-tool side of the ecosystem,
including the SanDisk dashboard and native-toolkit work. Follow that repository
for its source, deployment guidance and current device-validation status;
uploading source is not proof that every integration is hardware-tested.

Existing handheld adapter hooks are included here, but the separate drive
project is not vendored into GameHack. **Neither GameHack nor the Pi requires
a SanDisk drive.** The Pi remains the independent pinned USB worker.

## 🚧 Development build, not a magic wand

The story is playful. The status reports are not.

| Area | Current reality |
| --- | --- |
| Software regression tests | 65 handheld and 12 Pi tests pass in this source snapshot. |
| IR database | Installed; raw, NEC, and NECext conversion supported. Other parsed protocols are explicitly marked unsupported. Native transmission still needs testing. |
| IR carrier | The current Tiqiaa adapter uses a fixed ~36.6kHz carrier. Database frequencies cannot change that hardware limitation. |
| Pi USB networking | NCM validated on a PC. Handheld connectivity and Wi-Fi coexistence still need validation. |
| TF2 / expansion card | Not fixed: the handheld times out during controller initialization, before partitions or ROMs can be read. |
| 256GB TF1-only route | Restore, file comparison, bootloader and all filesystem checks passed; safely ejected. Native boot/gameplay pending; bypasses rather than repairs TF2. |
| Local OpenCode | Frontend installed; native provider execution and interactive compatibility remain to be verified. |
| Original Zero-Day feature set | Audited and partially adapted—not a claim that every upstream feature has been ported. |

Passing software tests does **not** mean every radio, adapter, or handheld
workflow has passed native hardware testing. We keep those receipts separate.

## 🗂️ Two operating systems, one repository

```text
GameHack-Zero/
├── README.md
├── hackeros-v3/          # Handheld OS, launcher, staging, tests, and docs
└── gamehack-companion/   # Pi companion OS, USB worker, and deployment helpers
```

Start with the project notes in each folder. On the handheld side:

- [`IR-DATABASE.md`](hackeros-v3/IR-DATABASE.md): database provenance, supported
  signals, adapter limitations, and deployment status.
- [`SD2-STORAGE.md`](hackeros-v3/SD2-STORAGE.md): debug/ROM layout and mounting.
- [`DARKOS-SD2-COMPARISON.md`](hackeros-v3/DARKOS-SD2-COMPARISON.md): TF2 evidence
  and why we aren't blindly copying device trees.

For the Pi, see [`NCM-TEST.md`](gamehack-companion/NCM-TEST.md) for USB networking
validation and rollback notes.

> **Source snapshot, not a flashable image:** this repository contains real source
> directories, not local symlinks. Card images, backups, keys, credentials, ROMs,
> compiled binaries and device logs are excluded. See [DEVELOPMENT.md](DEVELOPMENT.md)
> for dependencies and important deployment-script limitations.

## 🛟 Save before experimenting

Back up the system card before changing boot, kernel, or device-tree settings.
A full-card backup covers the bootloader and partition table too—not just the
visible files.

On the development PC, backups live under `hackeros-v3/backups/` (not uploaded).
An `.img.partial` is **not** a
finished backup. Completion requires the verified image and its checksum and
metadata files.

**Never publish card images, private pairing keys, provider tokens, credentials,
or private logs.** The companion's `access/` directory and system-card backups
need particular care. This README is not a substitute for checking every file
before pushing to GitHub.

## 🤝 Inspiration & credits

- [Zero-Day OS](https://github.com/jayis1/Zero-Day-OS-): the original toolbox
  concept behind this adaptation.
- [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB): community infrared
  remote data. The database is an external dependency, not vendored here; upstream notes that
  contributions before commit `2319685` are not covered by its CC0 declaration.
- Debian, Armbian, Raspberry Pi OS, Freedoom, Crispy Doom, OpenCode, and the
  open-source projects doing the real work beneath the boot screen.

Project lore does not replace licenses. Upstream components and data retain
their own license terms; this README does not grant a blanket license.

## 🧭 Keep the adventures friendly

Use radio/network auditing only on systems you own or are explicitly authorized
to test. Transmit IR only to devices you own or may operate. Prefer reversible
experiments, preserve the logs, and shut down cleanly before removing cards.

---

**The dev version that never existed. The project that now does.**

*Press R2 to continue. Press L2 if the dolphin asks for your Wi-Fi password.*
