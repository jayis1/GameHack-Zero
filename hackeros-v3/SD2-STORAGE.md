# GameHack Zero SD card 2

Prepared October 10, 2026 with explicit user authorization to erase the
255,869,321,216-byte removable card. Partitioning/formatting is not secure erasure.

| Label | Size | Filesystem | UUID |
| --- | --- | --- | --- |
| GHDEBUG | 32 GiB | ext4 | db0e4472-ba23-4523-9b61-2f9694211ce4 |
| GHROMS | 206.3 GiB | exFAT | 6ADB-B468 |

MBR partition table, PARTUUIDs `51cf3b58-01` and `51cf3b58-02`.
Debug root and folders are private to UID/GID 1000; storage is not encrypted.
Debug folders: sessions, journal, gamehack-zero, pi-worker, usb-network,
captures, crash-reports. Avoid credentials and private keys in diagnostics.

Game folders: roms/{doom,nes,snes,gb,gbc,gba,megadrive,mastersystem,gamegear,
psx,n64,arcade,psp}, bios, saves, screenshots. Official Freedoom 0.13.0 WADs
and license/credits were copied and byte-compared against staging/opt/freedoom.
No commercial ROMs, BIOS files or emulators were installed.

Both filesystems passed read-only checks after unmounting.
The SD2 system-card update mounts these exact UUIDs at `/data/debug` and
`/data/external`. The exFAT kernel module is installed. Missing SD2 is skipped;
a timer retries mounting and updates diagnostics once per minute. It keeps
up to 20 boot snapshots (five files per boot, each capped at 64 KiB). User-added
files are not pruned. Files include kernel USB errors, interface/route/rfkill
state, USB topology, storage, service states, and the Pi client's filtered
connection metadata. No task commands/output, credentials or packet captures
are automatically copied. Logs may contain network identifiers and are not
encrypted. Reports are owned by hacker, not written as root.

Primary journal logs remain on the 64GB card, capped at 32 MiB/seven days;
Armbian's volatile RAM-log mount is disabled while zram swap is retained.
FILES has a debug-log browser; PLAY has an SD2 ROM browser. Existing Freedoom
menu entries prefer the SD2 WADs and fall back to the system copies. Saves stay
under `/data/gamehack-zero/freedoom` to avoid losing access without SD2.
No additional console emulator is installed by this update.

FILES > Safely eject expansion stops automatic collection and unmounts both
partitions. Reboot to resume automatic mounting. Shut down before inserting
or removing cards if unsure. Native SD2 mounting remains to be verified on the
handheld. Pi boot logs must be retrieved separately.

## 4.2.0 card-side maintenance

The user subsequently added ROMs and BIOS/support files. Their earlier
organization moved 23 BIOS/support files to `/bios`, retained the Neo Geo
ROM-side BIOS dependency while adding a `/bios` copy, and prefixed 129 empty
folders with `X_`. The original organization manifest is retained on GHROMS.

During 4.2.0 maintenance, eight PSX CUE sheets were found to reference missing
track names because the actual BIN filenames used underscores instead of
apostrophes, with additional case differences in some files. Each reference
had exactly one existing match; only the CUE text was corrected. All 51 CUE
sheets now resolve their track files. ZIP central directories (1,908 archives)
were readable; full CRC/decompression and gameplay were not tested.

All 7,217 original inventory files remain accounted for. BIOS/Freedoom hashes
are unchanged, debug folder UID/GID 1000 and 0700 permissions pass, and empty
folder markings remain intact. Both partition READMEs now describe 4.2.0 rather
than incorrectly claiming that the mounting/collector update is not installed.
`SD2-4.2.0-MAINTENANCE.json` on GHROMS records the repairs and audit scope.
Original CUE sheets/READMEs are backed up on the PC under
`sd2-maintenance/20261011-020101Z/` in this project.

GHDEBUG still has no saved handheld reports: TF2 initialization is unresolved.
Partition layout, labels and UUIDs were not changed. These repairs address
card-side references/documentation, not the controller timeout.

## Physical 128GB replacement card

The user subsequently supplied a physical 127,865,454,592-byte card and
authorized erasing its Armbian installation. The 256GB resize experiment was
paused; that card remains unchanged. The new card was formatted into:

| Label | Size | Filesystem | UUID |
| --- | --- | --- | --- |
| GHDEBUG | 32GiB / 34,359,738,368 bytes | ext4 | 83809ff4-9ea9-46b0-bec0-14b719a09e61 |
| GHROMS | 93,504,667,648 bytes / ~87.08GiB | exFAT | 7ACB-F55A |

The full device including partition overhead is below 128GB decimal. MBR ID
`45aeb969`, partition starts 2048 and 67110912 (512-byte sectors). These UUIDs
are intentionally unique, not copies of the 256GB identifiers.

Private UID/GID 1000 debug directories and empty ROM/BIOS/save/screenshot
folders were created. The user will add games from Documents; no ROMs, BIOS or
WADs were copied during formatting. Formatting is not secure full-media erasure.
The saved old first-MiB/partition-table metadata is NOT a full Armbian backup.

`install-sd2-128-update.sh` refreshes only the system card's storage mount helper
and diagnostic UUID allowlist (with replaced-file backups), and copies these
notes. Both prepared cards remain supported by their exact UUIDs. The update
must be deployed to the 64GB system card before the new expansion browser and
collector can mount the 128GB layout. TF2 detection still needs native testing.
