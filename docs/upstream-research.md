# Upstream reconnaissance — 2026-09-19

## Enlightenment

[Official releases](https://www.enlightenment.org/download) list EFL 1.28.1,
Enlightenment 0.27.1, Terminology 1.14.0, Rage 0.4.0, Ephoto 1.6.0, Ecrire 0.2.0,
Evisum 2.0.12, Econnman 1.1, Python-EFL 1.26.1, Enventor 1.0.0 and EDI 0.8.0.
Build EFL before its consumers. These observed versions are not a verified
compatible set; in particular, review Python bindings against the selected EFL.

[Enlightenment's overview](https://www.enlightenment.org/) describes X11 as its
primary supported target and Wayland support as experimental.
[Upstream repositories](https://git.enlightenment.org/) are the next discovery
source for additional tools, modules and themes. Review activity, license,
dependencies and modern EFL compatibility before adding build requests.

The download page mixes release listings with older generic build guidance;
use each release's actual build files and Alpine recipes for dependency names
and musl/OpenRC integration. Do not copy glibc ldconfig instructions blindly.

## COSMIC

[Upstream desktop](https://github.com/pop-os/cosmic-epoch) and
[compositor](https://github.com/pop-os/cosmic-comp) are the primary sources.
Alpine's [edge cosmic-session contents](https://pkgs.alpinelinux.org/contents?arch=x86_64&branch=edge&name=cosmic-session&repo=community)
place the session in `/usr/share/wayland-sessions/cosmic.desktop`.
An [edge/community package](https://pkgs.alpinelinux.org/package/edge/community/x86_64/cosmic-session)
exists. Stable-branch availability was not established in this pass. COSMIC
is a separate Wayland session; Xwayland application support is not an Xorg session.

## Alpine packaging and media

[Release branches](https://alpinelinux.org/releases/) and
[aports](https://gitlab.alpinelinux.org/alpine/aports) own the base release and
recipes. Prefer aports recipes when available; package upstream sources when
needed, preserving native subpackages, hooks and dependency metadata.

Reference pages to read before implementation:
[Creating a package](https://wiki.alpinelinux.org/wiki/Creating_an_Alpine_package),
[custom ISO with mkimage](https://wiki.alpinelinux.org/wiki/How_to_make_a_custom_ISO_image_with_mkimage),
[COSMIC on Alpine](https://wiki.alpinelinux.org/wiki/COSMIC).
These wiki pages returned HTTP403 to the research tool; their detailed guidance
has not yet been verified. Do not claim those instructions were followed.

## Local reusable evidence

`../AuziX/auzix_rethink/docker/source-intake/desktop/enlightenment/APKBUILD`
contains the existing E27/X11 recipe. It is a recovery candidate, not copied
wholesale: review dependencies, nls setting, job control, checksums and all
upstream patches before importing. Recover EFL fixes from successful build
receipts/history, not the current failing broad path-conversion run.
