# E’ifyd installer source review

Reviewed 2026-09-20. This is a source review and implementation direction,
not a claim that partition editing has been implemented or tested.

## Sources actually inspected

- Ubuntu Ubiquity, official https://git.launchpad.net/ubiquity,
  commit `8972fb341cc3bd2be41630b80936ccc69d922d0f`:
  `ubiquity/plugins/ubi-partman.py`, `debian/copyright`.
  Bodhi publishes its installation flow at
  https://www.bodhilinux.com/w/installation-instructions/ and source pointers
  at https://www.bodhilinux.com/w/source-code/.
  The inspected code is upstream Ubiquity, not a verified current Bodhi patchset.
- https://github.com/Elive/elive-tools,
  commit `a3e24cb5f27800af966b84e5f9c9ff9c9a885034`:
  `usr/lib/elive-tools/functions` explicitly defaults its GUI helper to Zenity,
  with Yad also configured. This does not establish the toolkit of every
  current Elive installer dialog.
- https://github.com/Elive/skeleton-c-elm,
  commit `081cdb176642617de325ae360e38e85cca8325c3`:
  `autofoo/src/bin/efl_hello_world.c` and `autofoo/COPYING`.
  This is an Elementary application skeleton, not partitioning code.
  It demonstrates app data-directory registration, theme selection,
  command-line handling and Eina logging. Its notice permits redistribution
  under two conditions retaining notices (BSD-style).
- Elive developer discussion, February 2020:
  https://forum.elivelinux.org/t/calamares-vs-eliveinstaller-vs-others-brainstorming/1839
  describes the installer and points to the installed `eliveinstaller-6g`
  package's functions file. That installer package itself was not retrieved;
  its code and license remain unverified. The legacy source browser was
  inaccessible through the web tool.

Downloaded review checkouts are under `/tmp/eifyd-upstream-review`; they are
not project dependencies. No upstream installer was executed or copied in.
Ubiquity's copyright file identifies GPL version 2 or later, with component
notices: any direct code reuse needs the relevant notices preserved. Our
current proposal borrows behavior, not its Debian-specific implementation.

## What the source teaches us

Ubiquity's `initialize_resize_mode()` receives minimum, maximum and preferred
sizes from its backend and further bounds the maximum by installation space.
The slider does not invent filesystem limits. Its `edit_partition()` carries
size, method, mount point and format as separate fields. Its backend handles
`partman/confirm*`; copying this plugin would also import assumptions about
Debian partman/debconf, rather than simply giving us a portable disk dialog.

Our existing `aports/eifyd-installer/eifyd.c` already uses Elementary and
launches the Python adapter with separate arguments. Keep that foundation.
The current backend only supports whole-disk `setup-disk`; it cannot yet
honor arbitrary partition rows or preserve a selected home partition.
Do not expose those controls as working until the adapter supports them.

## Apply to our existing installer

1. Collect choices into one installation plan: storage, boot, account,
   package groups, optional migration. Both review and execution consume it.
2. Storage uses an Elementary partition list with an edit dialog: mount point,
   filesystem, size entry and slider sharing one bounded value, and explicit
   Format checkbox. Reusing a filesystem and formatting it are distinct.
   Default new layouts to separate root/home with ext4; firmware determines
   the boot partition requirements. Existing home preservation must appear
   explicitly in the review.
3. Boot settings show detected BIOS/UEFI mode and the GRUB destination or EFI
   system partition. Do not assume a whole-disk device is an EFI partition.
4. Gather account/password and package-group choices before execution.
   Use existing canonical package profiles; do not create another catalog.
5. Migration opens a secondary dialog, selecting source user folders and
   destination. Keep it optional and distinct from formatting decisions.
6. Show one final review containing concrete create/resize/format/mount/boot
   actions. One destructive confirmation authorizes that reviewed plan;
   changing it invalidates the confirmation. Keep errors actionable without
   repeating all earlier questions.
7. Elementary supplies the pages, lists, entries, sliders, checkboxes and
   confirmation popup. Python continues to adapt native Alpine tools.
   Add manual-layout support to that adapter rather than copying partman or
   writing a second installer. Keep the existing whole-disk path working.

The next implementation unit is the shared plan plus read-only storage
editor/review in the current GUI. Then connect its accepted layout to the
Alpine installation path and validate on a disposable disk. An attribution
page should describe actual component licenses, not invent an Alpine EULA.
