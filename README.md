# 🐬 GameHack Zero

### Controller-first handheld OS with a two-Pi companion system

**Updated 14 October 2026 · GameHack Zero 4.2.0 development beta.**

## 🎮 The handheld is becoming its own development machine

OpenCode runs **on GameHack itself**. The owner is signed in and using Build to
inspect the actual hardware, improve the OS, write documentation and prepare
scripts for local installation—not just use a remote coding demo.

Reviewed on-device work includes hardware-aware settings, workload power
profiles, thermal fallback, quieter diagnostics, emulator/media defaults and
idle terminal-redraw optimization. These changes are installed on the development
card; performance gains and broader gameplay acceptance still need native tests.

**Another owner-created whole-OS update batch is waiting to be reviewed.** We
will read its documentation/scripts and preserve its changes before merging
further updates. Unreviewed work is not yet advertised as validated functionality.

### Latest handheld milestones

- **YouTube:** owner-confirmed working video playback after the isolated JS/EJS
  resolver fix and low-resolution H.264 preference.
- **Simple browser:** Links text browsing installed; native HTTPS and terminal
  mouse transport passed. No JavaScript-heavy sites or web video are promised.
- **OpenCode links:** X → Open visible web link → review → browse → return to
  the existing coding session. Not a system-wide URL opener or an OAuth browser.
- **L3 review:** installed through a narrow backed-up merge preserving native
  tuning/redraw work. L3 toggles review; D-pad up/down pages through long answers
  and questions; L3 returns to typing. ARM behavioral checks passed; actual
  on-device controller acceptance is still pending.
- **Optional menu sounds:** default muted, selectable volume, with audio release
  before games/media; native handoff testing remains a separate gate.

## Current architecture

```text
GameHack Zero / R36XX onboard Wi-Fi
  └─ trusted Wi-Fi, strictly pinned SSH → Pi A (32GB)
       └─ Pi A USB host/data → Pi B USB gadget (separate 32GB)
```

GameHack uses **internal Wi-Fi; IR is the only external handheld OTG device in
supported scope**. Jellyfin is the intended media-center client, filling Kodi's
role. Compatible dArkOS code is reused without replacing the working board profile.

**Pi A:** Zero W Rev 1.1; native pinned Wi-Fi SSH works. Its Waveshare 2.13-inch
monochrome V4 dashboard is installed, with original A/B mascots and owner-confirmed
portrait orientation. PiSugar S supplies no software battery percentage/voltage;
button/shutdown integration and the Pi A→Pi B power budget remain unverified.

**Pi B:** distinct image verified and flashed to its own card. Native enrollment,
radio capability checks and Pi A→Pi B relay remain pending; the data cable is
awaited. Active labs must never autostart on boot, restart or cable attachment.
Activation must be explicit GameHack → pinned SSH Pi A → Pi B. Wi-Fi monitor
support and Bluetooth HCI/over-air limitations must be capability-tested.

Trusted home Wi-Fi is the current test network. The SanDisk media drive's AP is
the intended final shared network, subject to client-to-client connectivity.
No automatic LAN trust, key replacement or handheld USB fallback.

**Retired on handheld:** direct Pi USB pairing, hubs, USB mode switches,
Bluetooth dongles and external capture radios. Essential USB support for
onboard Wi-Fi stays. Pi A's temporary PC recovery and Pi A→Pi B link are separate.
IR transmission and Wi-Fi/IR coexistence still require native tests. Independent
exact-board firmware reproduced the cable/Wi-Fi failure; no software-only fix is claimed.

**Safety:** preserve 256GB GHROMS/GHDEBUG, ROMs, saves, accounts, keys and setup
progress. Never whole-flash a fresh image over that library. Fresh builds
preformat four volumes; automatic smaller-image expansion is not implemented.

**Source ≠ installed card ≠ release image.** A corrected fresh handheld image
passed build checks but is not natively boot-qualified and predates the latest
resolver/browser/tuning/L3 work. Older images and this sanitized executable
export may lag the live card. Updating this README does not synchronize all
code, publish a new image, or declare every feature complete.

Start with [handheld overview](hackeros-v3/README.md) and
[Pi A/Pi B overview](gamehack-companion/README.md).
The narrative below is historical background; its earlier USB workflows and
status descriptions are **not current deployment instructions**. Use the current
architecture and status above for the two-Pi design.

### Historical inspiration: an independent Linux project, not Flipper firmware

**A Linux handheld, a tiny Pi sidekick, and a suspicious amount of ambition.**

**Consolidated development release: GameHack Zero 4.2.0.**
See [release notes](hackeros-v3/staging/opt/hackeros/RELEASE-4.2.0.md) and the
[deployment checklist](RELEASE-4.2.0.md).
This is a development version, not a declaration of finished hardware support.

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
| **Pi A** | Zero W: pinned Wi-Fi SSH worker, e-paper dashboard, future USB host for Pi B. |
| **Pi B** | Separate card/identity; image flashed, native enrollment and relay testing pending. |
| **USB-C IR accessory** | External infrared adapter; the sender implementation targets Tiqiaa/Tview hardware with USB ID `10c4:8468`. |
| **64GB comparison card** | Repurposed with explicit approval for exact-board firmware research. |
| **Two 32GB Pi cards** | Independent Pi A and Pi B systems and identities. |
| **256GB single-card route** | Protected primary TF1 system; native boot, Wi-Fi, coding and YouTube observed. |
| **128GB expansion card** | Prepared ROM/debug storage for TF2; native TF2 detection remains unresolved. |

The handheld is the captain. The Pi is the crew—not a replacement for the
handheld's Wi-Fi, and not an excuse to require SSH for every interaction.

## 💾 256GB single-card route — TF1 only

The current development route puts the handheld OS and libraries on **one 256GB
card in TF1**, leaving TF2 empty. This bypasses the TF2 initialization failure;
**it does not fix TF2**. The 64GB card was later repurposed for firmware comparison.

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
was safely ejected at that checkpoint. Native TF1-only boot, Wi-Fi, OpenCode and
YouTube have since been observed; broader gameplay acceptance remains pending.
Do not treat this README as a completed
hardware test or an instruction to flash an older release image.

The draft image assets and public source snapshot do **not** yet contain a newly
validated 256GB build. No updated flashable image is being announced here. A
migration must preserve ROM/BIOS data before recreation—exFAT cannot safely shrink
in place. A single reader can be used sequentially via verified PC-held copies.

## 🧰 What's in the toolbox?

- **Controller-first launcher:** menus, on-screen keyboard, themes, favorites,
  and recent actions. **L2 goes back. R2 says yes.**
- **Networking workflows:** internal Wi-Fi setup, pinned SSH and diagnostics.
- **Pi A worker:** Wi-Fi-only, explicitly enrolled, strictly pinned SSH;
  handheld enrollment and the later Pi B relay remain incomplete.
- **Infrared library:** 8,901 remote files from
  [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB), adapted for GameHack's
  remote-and-button selection UI.
- **Local coding frontend:** an on-device terminal, controller keyboard, and
  OpenCode Build with R3 mouse and L3 review. Cloud providers still need internet
  and credentials; system changes still require Linux permissions.
- **Media/web:** working YouTube, intended Jellyfin client and lightweight text browsing.
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
a SanDisk drive.** Pi A is controlled through pinned Wi-Fi SSH; the SanDisk AP is
the intended later shared network, not a requirement for current home testing.

## 🚧 Development build, not a magic wand

The story is playful. The status reports are not.

| Area | Current reality |
| --- | --- |
| Software regression tests | Latest private checks: 263 handheld source tests, 127 image tests, plus 25 merged terminal/browser tests and redraw checks. These counts do not qualify the lagging executable export. |
| IR database | Installed; raw, NEC, and NECext conversion supported. Other parsed protocols are explicitly marked unsupported. Native transmission still needs testing. |
| IR carrier | The current Tiqiaa adapter uses a fixed ~36.6kHz carrier. Database frequencies cannot change that hardware limitation. |
| Pi A networking/display | Native pinned Wi-Fi SSH works; portrait V4 e-paper orientation confirmed by owner. |
| Pi A→Pi B | Pi B image flashed; cable, power safety, enrollment and explicit relay remain pending. No automatic active labs. |
| TF2 / expansion card | Not fixed: the handheld times out during controller initialization, before partitions or ROMs can be read. |
| 256GB TF1-only route | Working protected system; latest narrow L3 update passed clean checks. Bypasses rather than fixes TF2. |
| Local OpenCode | Owner signed in and developing OS changes; L3 installed, native review-button acceptance pending. |
| YouTube | Owner confirms working video; not a claim of all-codec/Jellyfin/hardware-decoding acceptance. |
| Whole-OS tuning | Reviewed native changes preserved; next owner-created batch awaits documentation/script review. |
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

For the Pi, start with its [role/access overview](gamehack-companion/README.md).
[`NCM-TEST.md`](gamehack-companion/NCM-TEST.md) records historical recovery-link
tests, not instructions for direct handheld→Pi USB pairing.

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
- dArkOS/ArkOS contributors: compatible handheld code and platform research,
  adapted with per-component licensing, not a blanket license.
- Links, QuickJS-NG and yt-dlp/EJS: lightweight browsing and media resolution.
- Bjorn and Waveshare: reused display-driver work with notices retained;
  GameHack's dashboard mascots are original.
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
