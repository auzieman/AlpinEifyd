# AlpinEifyd — AlpinE / E’ifyd

AlpinE / E’ifyd is the bridge release toward AUZiX and an alternate Alpine-native
edition. See [public release and portable builds](docs/public-release.md).

An Alpine-native Enlightenment desktop distribution, with an optional COSMIC
session. Initial architecture: x86_64. A live workstation is under review in VM145;
this is not yet a validated laptop installation release.

AlpinE is an additive spin: official Alpine main/community provide the normal
system; our signed repository supplies only our additions and explicit backports.
The install image and repository-only installation consume the same desktop
metapackages. See [repository and image design](docs/repository-and-image.md).
Public source: [auzieman/AlpinEifyd](https://github.com/auzieman/AlpinEifyd).
See [source scope and licensing](NOTICE.md) and the [source snapshot](docs/source-snapshot.json).

## Watch the AlpinE’ifyd walkthrough

[Watch on YouTube](https://youtu.be/JF7gO9Wty5I): a conversation about
“Imitated Intelligence,” FHS and the unpaved road of custom Linux layouts,
followed by a tour of the AlpinE Enlightenment workstation.

## Scope

- Enlightenment on X11 is the primary desktop.
- Preserve Alpine's normal filesystem, musl, OpenRC, APK transactions and
  native abuild packaging, including subpackages and hooks.
- Use Alpine's installer and image tooling behind the E'ifyd Elementary interface.
- Build a broad EFL application collection; keep compatibility patches with
  the individual APKBUILD that needs them.
- Package themes, wallpapers and defaults as ordinary APK-owned assets.
- COSMIC is an optional Wayland session, not an X11 window manager.

AUZiX remains a separate, preserved project. Its build evidence and portable
upstream fixes are useful inputs; its path-transformation machinery is not a
dependency of AlpinE. Nothing in this project requires moving AUZiX to an attic.

## Small pieces

| Location | Responsibility |
| --- | --- |
| `catalog/everse.json` | Researched application candidates and build status |
| `catalog/sources.json` | Official source URLs, local mirrors and development branches |
| `profiles/*.json` | Desktop selections; dependency closure belongs to APK |
| `aports/` | Native APKBUILD recipes and adjacent patches, when imported |
| `docs/` | Decisions, upstream references and acceptance evidence |

Use native abuild to build and sign packages. Install through APK. BKC delivers
and runs these commands with retained logs; it does not become another packager.
Package selection must not change how a package is built.

## First milestones

1. Select one Alpine release/toolchain and pin aports plus source checksums.
   Existing 3.22 E build evidence is a reference, not a claim it is the best
   release for the new edition. Verify COSMIC availability before selecting it.
2. Recover the successful EFL/Enlightenment/Terminology recipes and musl fixes,
   preserving provenance. Remove AUZiX path changes from the copies only.
3. Build signed native APKs and install them in a clean Alpine container.
4. Prove an X11 Enlightenment login in a VM: terminal, file manager, networking,
   sound, menus, session restart. A container CLI check is not desktop proof.
5. Add E applications in small groups. Then compose install media through
   Alpine tooling; evaluate COSMIC independently on the same selected base.

Local Gitea hosting, native package builds and live workstation updates run through
BKC. The canonical selections are image/packages and image/workstation-flatpaks.
Public media is built from that selection and published after a fresh VM boot
and desktop validation; see the public release document for acceptance limits.

## Companion projects

- [E-Jamz](https://github.com/auzieman/E-Jamz): native EFL music player, rack-style EQ and playlists.
- [BlackKnight E Theme](https://github.com/auzieman/BlackKnight-E-Theme): theme tools and original wallpapers.
- [AUZiX / AlpinE public home](https://auzix.auzietek.com/alpine/): release status, signed repository and media.

## Source preview

This repository is a public source snapshot, not a new boot-image release.
The retained third-party EDJ theme collection is omitted pending per-asset
redistribution verification. Its recipe and checksums remain for provenance;
the full `build/public-order` requires those verified assets before it can build.
The core `build/order` does not require the theme collection.
Local laptop plans and lab receipts are not portable installer inputs.
See [public release notes](docs/public-release.md) for validation limits.
