# TF2 investigation summary (sanitized)

The tested R36XX uses the ff380000 DesignWare MMC controller for TF2 and
ff370000 for TF1. With the physical 256GB expansion card inserted, TF2 produces
error -110 during initialization and clock-update command 0x202000 times out.
No second-card block device appears. The same inserted-card test is reproducible;
an empty-slot boot had no corresponding initialization errors.

0x202000 is UPD_CLK | PRV_DAT_WAIT, not a card CMD0 response. Later debugfs
snapshots are post-failure state, not measurements at the instant of timeout.
TF1 and TF2 share regulator references in the active tree; do not change those
voltages blindly. Identification-frequency retries already reach 100kHz, so a
lower maximum transfer speed is not a demonstrated fix.

dArkOS references contain similarly configured SD2 nodes and matching supply
constraints; no proven fix was identified. A subsequently supplied Armbian
128GB card also had matching relevant controller/regulator nodes. Its original
layout was erased with authorization to prepare a 32GiB ext4 GHDEBUG and
remaining exFAT GHROMS comparison. The new mount-ID update is staged, but its
native detection test is still pending.

No device journals, private snapshots or firmware images are uploaded here.
This summary deliberately avoids presenting reference DTB differences as a
proven repair. Do not reformat working ROM storage to solve a failure occurring
before the partition table can be read.
