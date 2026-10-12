# E'ifyd raw USB image

Uses Alpine's packaged alpine-make-vm-image tool on Alpine 3.24.2.
Native APK installs the image/packages selection from main/community plus our
signed repository. Alpine's tool owns partitioning, filesystem, kernel,
initramfs and bootloader. No ISO or custom disk writer.

The current template produces a partitioned 8GiB sparse raw BIOS image with the LTS
kernel and USB, NVMe, ATA and virtio boot support. BOOT_MODE=UEFI selects the
upstream tool's separate UEFI mode; this is not a dual-firmware image.

BKC pipeline alpine-raw-image verifies the published signed feed,
then runs image/build.sh in a native Alpine builder on R730. Public keys only
are copied into the image. APK inputs have a persistent cache.

The skeleton adds E'ifyd text, repository configuration and LightDM/E settings.
configure.sh registers native services with rc-update. Live local user alpine
autologins and can use doas without a password; root has console access with
no password, like installation media. No SSH server is enabled. These are
live-media defaults, not installed-system account policy. Before accepting
a permanent install, verify password setup and remove live autologin/doas
policy. The E'ifyd APK supplies the Elementary interface and a native setup-disk
adapter; see ../docs/installer.md. A disposable installation and boot to the
installed login greeter passed; preserved-home reinstall and physical hardware
installation remain separate acceptance work.

Required build environment: ALPINE_REPOSITORY_KEY and OUTDIR.
ALPINE_REPOSITORY_URL defaults to https://auzix.auzietek.com/alpine/repo/v3.24;
an explicit override supports private builds. BKC checks the public index and key
against the selected package build before producing media. Use the
alpine-public-mirror pipeline to publish that signed feed first.
The pipeline supplies the public key and output directory. It records image SHA256 and package inventory.
VM145 runs the live workstation; earlier reference disks remain retained. Each
public image must pass a fresh boot and the non-repairing desktop check before
publication. The standard E profile supplies its PolicyKit authentication agent;
the image does not start a second GNOME agent. The public live selection uses
native Geany plus the requested multimedia tools. The workstation Flatpak
selection now includes OpenShot from Flathub; native FFmpeg, Audacity, Shotcut
and OBS Studio are selected in packages. Audacious with its OpenMPT tracker
decoder, openmpt123 and GStreamer codec/PipeWire plugins are also selected. This selection change has been tested
on the laptop; a rebuilt public image still requires its normal boot validation. Native desktop apps and the full theme collection
remain selected. The final hook cleans download caches and unused runtimes.

Light native productivity additions are Geany (code/text), Galculator
(scientific calculator), MuPDF (documents) and Xarchiver (archives). These use
the matching Alpine repository; no additional Flatpak runtime is needed.

Source: https://github.com/alpinelinux/alpine-make-vm-image
