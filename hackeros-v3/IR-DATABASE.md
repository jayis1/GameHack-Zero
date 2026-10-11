# GameHack Zero IR database

## State

Integration is **installed on the 64GB card** after inspecting its new boot logs.
All database files were verified byte-for-byte and seven installed ARM64
parser/conversion tests passed under emulation. Native UI/transmission remains
unverified; software conversion is not proof of device compatibility.

Source: https://github.com/Lucaslhm/Flipper-IRDB
Pinned commit: `d126fb1b6f1e114c52b4a8c19839ea65e3a9c24d`.
8,901 `.ir` remotes are staged with upstream README, LICENSE and source metadata.
Upstream explicitly excludes contributions before commit `2319685` from its
CC0 declaration; the complete database must not be described as uniformly CC0.
Original remote files are retained unchanged.

## Controls and integration

Infrared → Browse remote library opens GameHack Zero's category/brand/model
browser, model/brand search, or saved/learned remotes. Selecting a remote opens
its button list. **L2 = back; R2 = select** using existing controller navigation.
Each send requires confirmation and sends just the selected button once.
There is no automatic power-code sweep or background transmitter.

The system-card database is `/usr/local/share/gamehack-zero/ir-database`.
It does not require SD2 to enumerate. Learned remotes stay under
`/data/gamehack-zero/ir`; user-provided remotes on SD2 remain supported.
The privileged sender accepts only existing allowed data locations or the
installed database and validates a numeric button index.

Supported: raw timings, NEC and NECext (four-byte little-endian address and
command fields). NEC includes inverse bytes; NECext preserves both 16-bit fields.
Multi-button files can no longer silently transmit their first raw entry.
Other parsed protocols and malformed/oversized signals are marked unsupported
before USB transmission, rather than guessed or silently converted.

The Tiqiaa Tview 10c4:8468 sender uses its existing fixed ~36.6kHz carrier;
the database cannot make this hardware variable-frequency. UI confirmation
shows requested versus actual carrier. Unsupported carrier matches may fail.
Use only devices you own or are permitted to operate.

## Software audit

Every remote parsed without a file-level error. Current encodable buttons:

- 143,918 NECext
- 9,587 NEC
- 131,239 raw

31,576 encodable raw buttons request a frequency outside 35–40kHz, a diagnostic
range rather than a guaranteed compatibility boundary. Detailed rejections are
in `GAMEHACK-AUDIT.json` beside the database, including other protocols, malformed
hex fields and signals exceeding the adapter's 1,024-byte packet capacity.
60 local regression tests pass, including seven IR parser/conversion tests.

## Next deployment

First inspect the upcoming 64GB-card boot logs, including the SD2 diagnostic.
Identify the system card by root UUID
`2ac15f87-aa0e-4fa6-9437-b542636d070c`, not a guessed device path.
Mount at `/mnt/gamehack-debug` and invoke `install-ir-database-update.sh` as root.
The installer backs up affected code, refuses to overwrite an existing database,
verifies database bytes and checks that the active DTB hash remains unchanged.
Validate installed ARM64 code and units, then unmount, check filesystems and
safely eject. Kernel, USB role and pairing identities are not changed.
