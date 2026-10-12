# AE-002: additive repository and install image

## Package ownership

Official Alpine repositories provide the kernel, firmware, libc, package tools,
OpenRC, networking, Xorg, ordinary libraries and applications. Keep their native
paths, configuration and feature support. A minimal default selection is not a
stripped or incompatible base; users retain normal `apk add` capabilities.

Our repository contains only:

| Package/group | Purpose |
| --- | --- |
| EFL/E applications unavailable in the chosen release | Native recipes; explicit source backports or upstream releases |
| `alpine-spin-branding` | AlpinE artwork and modest visual branding; preserve Alpine release identity |
| `alpine-spin-themes` | Selected E/Elementary themes with attribution and source |
| `alpine-spin-wallpapers` | Selected wallpapers with attribution and source |
| `alpine-spin-desktop-defaults` | Menus, session defaults and first-user defaults; preserve subsequent user edits |
| `alpine-spin-desktop` | Minimal X11/E desktop metapackage |
| `alpine-spin-everse` | Optional wider E application collection |
| `alpine-spin-workstation` | Optional key productivity applications |

Names above are proposed package identities, not existing installable packages.
Avoid replacing official packages unless a specifically recorded compatibility
fix/backport requires it. Keep patches beside the responsible APKBUILD.

## Small factory

The controller selects our recipes, orders their declared local dependencies,
checks cached inputs/artifacts and invokes native abuild as an ordinary builder
user. Abuild owns fetching, checksums, preparation, compilation, splits and APK
emission. APK owns dependency transactions. No custom source path conversion,
archive repackager or replacement dependency solver.

Record source/recipe/patch/toolchain/dependency identities with each output.
Retain successful artifacts and retry changed/failed inputs only. Development
and runtime dependencies remain distinct. Validate native signatures, install
the produced packages on the chosen Alpine base, and check the selected desktop.

## Repository and mirrors

Use a release-specific repository with architecture directories and native
signed indexes/APKs. The actual Alpine release, repository URL and public-key
fingerprint must be fixed before producing installation commands.

Publish recipes, patches, licenses, public signing key, checksums and build
receipts alongside releases. Mirror immutable package/index sets together so
clients never receive an index referencing absent files. Keep private signing
keys outside source, images and mirrors. Mirror operators may copy the signed
repository unchanged; independently rebuilt packages use their own signing key.

Do not duplicate Alpine main/community into our package repository. The image
may include the official packages needed for installation without making us
their upstream maintainer. Offline installation coverage is a separately tested
image property, not implied by the presence of a repository URL.

## Install image and existing installations

The selected delivery medium is a bootable USB thumb drive. Installer branding
is E'ifyd; retain Alpine identity and its native installer behavior underneath.
The image and installed system must both receive the public repository key,
matching-release Alpine repositories and the AlpinE repository configuration.
Use the existing profile lists for package selection. Finish theme/wallpaper
packaging first, then integrate branding and repository setup into the image.
Offline package coverage remains a separate choice and validation requirement.

Use Alpine aports `mkimage` with a small AlpinE profile/overlay, official
repositories for the selected release and our extra signed repository. Keep
Alpine's normal installer; add branding, the package selection and documented
desktop setup rather than writing a new installer.

An existing matching Alpine installation should be able to trust our published
key, add our repository and install the desktop metapackage. Both routes require
the same documented service/session setup. Prefer upstream Alpine setup tools;
package hooks must not silently repartition disks or overwrite user settings.

Prove both routes: fresh VM installation plus reboot, and add-on installation
on a stock Alpine VM. Check E/X11 login, networking, audio, terminal, application
menu and package updates. COSMIC remains a separate optional Wayland profile.

## Default selection

Start with EFL, Enlightenment and Terminology; E provides its file manager.
Select one browser and a small editor/image viewer set after checking native
availability. Firefox, LibreOffice and the wider E collection remain explicit
workstation/optional choices rather than making every image large. The exact
minimal/key-app boundary is tracked in profiles, not hidden in build scripts.

## Upstream references

- [abuild and helpers](https://wiki.alpinelinux.org/wiki/Building_packages)
- [APKBUILD reference](https://wiki.alpinelinux.org/wiki/APKBUILD_Reference)
- [Custom ISO with mkimage](https://wiki.alpinelinux.org/wiki/How_to_make_a_custom_ISO_image_with_mkimage)

The upstream mkimage documentation exposes both normal and extra repository
arguments. Check the selected aports revision before generating commands.
