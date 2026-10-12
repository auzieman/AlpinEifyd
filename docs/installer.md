# E’ifyd workstation installer

E’ifyd 0.2 uses native Elementary pages and a shared Python installation API.
The package entry point is `eifyd-installer`. The live workstation in VM145
is the current review environment; this is not yet a public stable release.

## Graphical flow

- **Welcome:** scope, backup reminder, component licensing and console entry.
- **Disks & boot:** choose a detected disk. The new-layout mode creates GPT,
  firmware-appropriate boot support, a 1 GiB ext4 boot partition, configurable
  ext4 root and ext4 home using the remaining space. The root entry and slider
  share a value. Existing-partition mode retains the partition table, formats
  the selected root, and preserves home unless its Format checkbox is enabled.
  An optional ext4 boot partition and existing EFI system partition are supported.
  EFI is never formatted in existing-partition mode.
- **Your account:** hostname, username, timezone and matching password fields.
  The account receives sudo access; root login remains locked. Live autologin
  and passwordless sudo rules are removed.
- **Software:** optional groups expand to per-package selections. Core Alpine,
  E/X11, hardware/network/audio support and recovery tools stay in the live
  APK world. Native APK resolves dependencies; selection does not repack packages.
- **Review:** shows actual devices, format/keep operations, firmware/GRUB target,
  account and application selection. A password-free plan can be saved.
- **Install:** one final destructive confirmation, then native command output in
  the progress page. No installation starts merely by opening or reviewing.

Review binds the plan to disk identity, size and partition UUIDs. Installation
rechecks that identity after preparing the overlay and dependencies. Mounted,
read-only and active mapped targets are rejected. Existing home must be ext4;
an existing chosen user's directory must have the expected UID/GID. Its files
and settings are not overlaid by the default home skeleton.

GRUB mode follows how the live session was booted. BIOS/GPT requires a BIOS boot
partition; UEFI requires an EFI system partition. Existing-partition mode keeps
the other partitions, although installation writes the selected bootloader and
kernel paths. No resizing, encryption or LVM creation is performed by E’ifyd;
GParted is offered for separate layout preparation. Reopen the installer after
changing partitions externally to refresh its device menus.

## Shared backend

`eifyd_storage.py` normalizes plans and describes/applies native disk operations.
`eifyd-install` prepares the configuration overlay, accounts and software,
then calls Alpine's mounted-root `setup-disk` interface. Native Alpine still
owns APK installation, initramfs and GRUB installation. The new-layout adapter
uses sfdisk, mkfs and mount; it does not implement a filesystem or APK engine.

Optional package membership is data in `package-groups.json`, using package
names from the live image's canonical selections. The target APK world comes
from that live system, filtered by these explicit choices. Flatpak applications
and runtimes are copied from the live image and unselected apps removed from
the target. Network access to configured signed APK repositories is required;
this is not an offline-install guarantee.

The API accepts a JSON request on stdin:
`{"plan": {...}}` for review, or `{"plan": {...}, "token": "...", "password": "..."}`
for installation. The graphical frontend uses private pipes; passwords do not
appear in command arguments, saved plans or displayed progress.

Console: `sudo /usr/libexec/eifyd-install tui`. This is a line-oriented interface,
sharing the same layout, account, selection and execution logic.

For BKC or manual CLI use:

1. Save the plan from Review or the console.
2. Run `/usr/libexec/eifyd-install review --plan plan.json`.
3. Inspect its output and exact `REVIEW_ID`.
4. Execute `sudo /usr/libexec/eifyd-install install --plan plan.json --accept-plan REVIEW_ID --password-fd 3`,
   supplying a password through inherited descriptor 3, not an argument.

Any changed plan/disk requires a new review ID. An installed password-free
receipt is stored at `/var/lib/eifyd/installation.json`. Installation errors
stop the operation; a partial install is not reported as complete.

## Validation and release boundary

Local tests cover overlay account cleanup, disk-use rejection, identity-bound
confirmation, partition alias rejection, filesystem preservation constraints
and filtering optional versioned APK world entries. Native builds and GUI
screenshots are recorded in the work log. The BKC `alpine-installer-proof`
pipeline exercises only its marked disposable disk, then boots it as VM146.

BIOS/UEFI, reinstall preservation and actual boot results must be recorded
separately. A compiled package or an open window is not installation proof.
Migration is still a separate future dialog; no Windows/home data is harvested
automatically. No physical laptop disks are test targets.
