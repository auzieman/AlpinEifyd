# Initial decisions — 2026-09-19

User requested a separate, scaled-back Alpine/E distribution and upstream
research, potentially patching additional EFL applications. Primary session is
X11. COSMIC is an optional alternate desktop with its own Wayland session.

Standard Alpine paths, APK and OpenRC are the baseline. No AUZiX installer or
filesystem conversion. Themes and other reusable desktop assets may be brought
over with provenance and license checks. Keep APKBUILDs native and small.

Later user decision: reuse the AUZiX Elementary installer interface as E'ifyd,
adapted to native Alpine installation. The old filesystem/partition engine stays
out; see docs/installer.md for the native setup-disk adapter and proof status.

Open decisions: display/login manager and the COSMIC version supported by the chosen base.
Do not interpret open decisions as permission to mix release repositories.

Upstream version observations are discovery metadata, not a dependency lock or
proof of successful musl builds. Older E applications may require independent
patches or may remain optional; their absence must not silently shrink a profile.

## AE-002 clarification

Official Alpine repositories supply the base. Build/publish only AlpinE additions
and explicit missing/patched E packages. Keep the normal installer and provide
modest branding through packages. Offer the same desktop through an install
image and an additive, mirrorable repository. Minimal defaults and optional
workstation/Everse sets are data selections, not separate build engines.

## AE-004: branding and service model

Branding is AlpinE by Auzietek. Keep the core small. Recommend rootless Podman
for ordinary network services, with explicit persistent mounts and minimal
privileges. Containers share the host kernel; boot, kernel and hardware needs
are evaluated on their merits. Native Alpine services remain supported.
Use /etc for service configuration and /srv for persistent service data.
Initial documented patterns: nginx, separated web/PHP/database, scheduled
short-lived BusyBox tasks. Integrate host lifecycle through OpenRC.

Gitea on edge Kubernetes is the local source and package hub. Public upstream
E repositories have untouched pull mirrors, with separate writable development
forks. Replicate only selected public branches to Auzietek's GitHub repositories.
Public APK distribution on Auzietek uses ordinary HTTP-served signed repository
files. Do not infer authorization to publish every development branch.

## AE-007: first native build

Alpine 3.24 stable, starting with the 3.24.2 amd64 container pinned by manifest
digest in build/Dockerfile. EFL 1.28.1 and Enlightenment 0.27.1 reuse the prior
successful native recipes/source fixes. Terminology 1.14.0 uses the pinned Alpine
aports recipe documented in build/PROVENANCE.md. No edge binary mixing.
Installer branding direction: E'ifyd / Get E'ifyd — install AlpinE. Artwork/text
changes follow once the normal Alpine image and desktop package feed work.

## AE-011: USB installation media

User selected bootable thumb-drive installation media, as in the earlier work.
Keep Alpine's installer and installation semantics; apply E'ifyd branding to
installer-facing text/artwork and supply our package selection. This remains
Alpine with an additive AlpinE repository, not a replacement installation engine.
After the decorations are built, wire the signed repository/public key and
desktop package selection into both installation media and the installed target.
Keep official matching-release main/community enabled. No unsigned-repository
bypass. Verify USB boot and an installed-system reboot before calling it ready.

## AE-013: native raw disk media

Supersedes the initial ISO/mkimage implementation: use Alpine's packaged
alpine-make-vm-image for raw partitioned USB/HDD output. Start BIOS with LTS
kernel; UEFI is a separate supported output mode. No custom disk writer.

## AE-014: AUZiX continuity — 2026-09-20

AlpinE / E’ifyd is the working workstation reference for AUZiX’s intended user
experience. AUZiX’s canonical implementation root is ../AuziX/auzix_rethink.
Its additional responsibility is factory-driven source/build/package path
transformation while preserving the applications, themes, lifecycle behavior
and release workflow. Once proven, that factory may support a future AUZiX
refactoring of this desktop. Keep the current AlpinE release Alpine-native;
this decision does not start a path migration or declare installation complete.
See the AUZiX implementation README for the bounded challenges and open gaps.
