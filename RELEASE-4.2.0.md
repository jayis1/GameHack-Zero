# GameHack Zero 4.2.0 — deployment checklist

## Status

**Handheld deployed and verified; Pi release-marker deployment pending.**
The verified pre-release system-card backup is unchanged. After deployment,
all 8,948 payload files matched the manifest, 31 installed ARM64 tests passed
under emulation, and 182 protected boot/network/SSH files remained unchanged.
Both handheld-card filesystem checks passed and the card was safely ejected.
Native boot and hardware/provider tests are still pending.

- Handheld release: 4.2.0; 64 local regression tests pass.
- Pi companion release: 4.2.0; worker protocol remains 2; 12 tests pass.
- Optional SanDisk Nimbus FieldKit: existing independent v0.2 side project,
  not yet uploaded. This source snapshot retains the handheld menu adapter,
  not the separate project's full toolkit, firmware files or device reports.

Read the [full handheld release notes](hackeros-v3/staging/opt/hackeros/RELEASE-4.2.0.md)
for included features and unresolved hardware validation.

## Handheld

Reconnect the 64GB card. Identify root UUID
`2ac15f87-aa0e-4fa6-9437-b542636d070c` and boot UUID `1A45-2972`.
Inspect recent logs before changes. Mount root at `/mnt/gamehack-debug` and the
boot partition at `/mnt/gamehack-debug/boot/u-boot`; both must be writable for
installation. Never substitute a guessed `/dev/sdX`.

Run `hackeros-v3/install-release-4.2.0.py` as root. Its checksum manifest is
`hackeros-v3/release-4.2.0.json`; rebuild with `build-release-4.2.0.py` if sources
change. The installer verifies sources and destination bytes, saves replaced
files and checks the preserved DTB/boot configuration. It does not install
dependencies, flash media, edit networking profiles or erase user data.

Validate installed code and services, unmount boot/root, perform read-only
filesystem checks, then safely eject. Keep deployment status pending until done.

## Pi companion

The 32GB Pi card is a separate deployment. Identify root UUID
`5a4bdad1-138b-490f-b9a9-0bf50cb3847d`, inspect logs, mount at
`/mnt/gamehack-pi`, then run `gamehack-companion/install-release-4.2.0.sh` as root.
This refreshes the companion release marker/CLI only; existing NCM, radio
configuration, worker queue/results, SSH identity and base OS remain intact.
Validate installed ARMv6 code, check filesystems and safely eject afterward.

## Optional SanDisk

The separate Wireless Media Drive project has not been uploaded yet. GameHack's
menu adapter explicitly treats it as optional. No drive firmware, AP password, gateway,
Internet route or radio configuration is changed by the 4.2.0 update.
Post-reset connectivity and any secure custom device deployment remain separate
hardware work; the Pi does not require the SanDisk to run its USB jobs.

## Do not confuse a release with a hardware fix

TF2 remains blocked at controller initialization. IR transmission, native
OpenCode/provider operation, Pi-on-handheld NCM/Wi-Fi coexistence and Pi onboard
monitor capability still need verification. No blind voltage/DTB/kernel changes
are bundled in this release.
