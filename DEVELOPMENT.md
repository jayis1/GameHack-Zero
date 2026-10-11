# Developing from this source snapshot

## What is included

GameHack Zero 4.2.0 handheld source/configuration, controller UI, IR conversion,
storage collectors, worker client, tests and deployment helpers; Raspberry Pi
Zero W companion worker, NCM gadget configuration, radio helpers and tests.
The optional SanDisk project's full code/assets are not uploaded yet. Its
existing handheld menu adapter is retained without live-device documents.

This is not a downloadable OS/card image or a universal unattended installer.

## Tests

Handheld development needs Python, Pygame, evdev, pyte and Pillow (splash tool).
Use a virtual environment and install these dependencies through your normal
package-management workflow. On Linux:

```sh
mkdir -p /tmp/opencode
python3 -m unittest discover -s hackeros-v3/tests -v
python3 -m unittest discover -s gamehack-companion -p 'test_*.py' -v
```

Pygame tests use a dummy display. Fonts and a working PTY are also needed.
Some UI tests skip when optional UI packages are absent; a partial/skipped run
must not be described as full hardware validation.

## External dependencies not uploaded

- Official Debian/Armbian and Raspberry Pi OS images, kernel/DTBs and firmware.
- OpenCode native binary and provider authentication (never commit credentials).
- Freedoom WADs; `hackeros-v3/prepare-freedoom.py` prepares upstream assets.
- External wireless driver builds/modules; see preparation scripts and notes.
- Flipper-IRDB remote data. The tested database snapshot was commit
  `d126fb1b6f1e114c52b4a8c19839ea65e3a9c24d` from
  https://github.com/Lucaslhm/Flipper-IRDB. Restore the original `.ir` category
  tree under `hackeros-v3/staging/usr/local/share/gamehack-zero/ir-database/`
  locally, retaining upstream README/LICENSE and provenance. Its upstream CC0
  declaration excludes contributions before commit `2319685`.
- Pairing keys and pinned host identities: generate/verify your own. Do not
  turn off host-key checking to compensate for missing private setup files.

After preparing required assets, run `build-release-4.2.0.py` to create a local
manifest. A manifest built without the IR tree is not the complete installed
8,901-remote database payload.

## Deployment warning

**Do not blindly run the provisioning/flash/update scripts.** Several are
development-machine-specific: they contain absolute `/home/jais` paths, known
card UUIDs, fixed mountpoints, explicit device targets or a required local
verified-backup identity. The source snapshot intentionally retains those
guards rather than silently making destructive commands generic.

Review every script, supply the correct dependencies, positively identify your
own target card and preserve a verified whole-card backup before adapting it.
This repository does not include that backup, a pairing identity or installer
inputs, and is not expected to provision an arbitrary device unchanged.

TF2 remains unresolved on the tested handheld. The new physical 128GB card
has a staged UUID allowlist update, pending actual system-card deployment and
native testing. Do not advertise software tests as proof of TF2 or radio support.

## Publishing safely

The root `.gitignore` excludes OS images/release output, private image-validation
clones, pairing/provider credentials, Wi-Fi profiles, ROMs/BIOS, device logs and
build caches. Only the two reviewed USB NetworkManager profiles are allowlisted.
Environment examples remain trackable, but must contain placeholders, not secrets.
Keep downloadable images as reviewed release assets, never Git source blobs.

Ignore rules do **not** remove files already tracked or erase Git history. Before
publishing, review `git diff --cached` and check for tracked ignored files with
`git ls-files -ci --exclude-standard`. Never force-add private files. If a secret
has entered history, revoke/rotate it and review remediation before going public.

The repository is a sanitized snapshot separate from the live development
folders. Sync reviewed source changes deliberately; never mirror card images,
access folders, capture/vault contents or device log directories into it.
No blanket project license is assigned by this snapshot. Upstream code/data
retains its own licensing; choose an appropriate project license explicitly
before advertising reuse permissions.
