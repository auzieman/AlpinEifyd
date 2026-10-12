# AlpinE / E’ifyd — the AUZiX bridge release

AlpinE is a precursor to AUZiX and an alternate Alpine-native edition in its
own right. It supplies the workstation experience while retaining Alpine's
paths and native package tools. The AUZiX factory can later add its path
transformations without discarding this desktop, application set or installer.

Public home: **https://auzix.auzietek.com/alpine/**.

Public source: [AlpinEifyd](https://github.com/auzieman/AlpinEifyd).
Companion projects: [E-Jamz](https://github.com/auzieman/E-Jamz) and
[BlackKnight E Theme](https://github.com/auzieman/BlackKnight-E-Theme).

The public source snapshot omits retained third-party compiled theme assets.
Supply verified, checksum-matching inputs before the full public-order build;
see [NOTICE.md](../NOTICE.md).

## Watch the AlpinE’ifyd walkthrough

[Watch on YouTube](https://youtu.be/JF7gO9Wty5I): a conversation about
“Imitated Intelligence,” FHS and the unpaved road of custom Linux layouts,
followed by a tour of the AlpinE Enlightenment workstation.

## Contributing projects

The [source catalog](../catalog/sources.json) records public upstream URLs,
observed revisions and local development branch conventions. An observed Git
head is not necessarily the source used in a released APK: the corresponding
`aports/<package>/APKBUILD` source URLs and checksums identify build inputs.
[Build provenance](../build/PROVENANCE.md) records recipe origins and patches.

- [Alpine Linux aports](https://gitlab.alpinelinux.org/alpine/aports): native
  packages and build recipes; matching 3.24 main/community supply the base.
- [Enlightenment](https://git.enlightenment.org/enlightenment): EFL,
  Enlightenment, Terminology, Ephoto, Ecrire, Evisum and other E applications.
- [alpine-make-vm-image](https://github.com/alpinelinux/alpine-make-vm-image):
  native raw boot-image production.
- [Simotek's themes](https://github.com/simotek/Enlightenment-Themes),
  [Chris Ripp's themes](https://github.com/chrisripp/Themes) and
  [eslide](https://github.com/1wErt3r/eslide): collected theme/source references.
  Catalog inclusion does not mean every item ships. Retain per-asset attribution
  and establish redistribution terms for each shipped asset.

Our repository is additive. Do not rebuild or mirror all of Alpine to use it.
Publish our recipe sources and patches alongside APKs, preserving upstream
licenses and applicable corresponding-source requirements. Never export private
Gitea settings, signing keys, lab receipts or credentials as a public source kit.

## Portable native package build

Run on an x86_64 Linux Docker build machine. These commands use the existing
native build scripts; there is no second packaging engine. The Compose entry
point is newly prepared and still needs a clean-host build proof.

```sh
export BUILD_REVISION=bootstrap
docker compose build builder
export BUILD_REVISION=$(docker image inspect alpine-public-builder:local --format '{{.Id}}' | cut -d: -f2)
docker compose run --rm prepare
docker compose run --rm builder
docker compose up -d repository
```

The full custom recipe list is `build/public-order`; ordinary applications
remain official Alpine packages. Sources, APKs and signing material use separate
named volumes. Work completion markers are reusable only with the identical
compiler image ID; recompute BUILD_REVISION after every rebuild of the builder.
Keep the signing volume private and backed up. Do not use `down -v` casually.
The repository service exposes only the APK output volume, locally on port 8088;
it does not mount private signing material. Export the public `.rsa.pub` key
separately and publish its fingerprint through the release page.

## Boot image and public shelf

The existing `image/Dockerfile` and `image/build.sh` use Alpine's image builder.
Supply a reachable signed repository URL, its public key and an output directory
as described in [image instructions](../image/README.md). Image creation needs
loop/mount privileges on the build host; the package compiler does not.
For public media the repository URL must be public, not a lab IP. Produce BIOS
and UEFI artifacts explicitly; do not label a BIOS image dual-firmware.

The BKC `alpine-public-mirror` lane publishes web content, the signed APK
repository and public key under the isolated `alpine/` subtree.
`alpine-media-publish` compresses a boot-validated image, verifies its raw and
compressed hashes, and publishes immutable downloads plus SHA256 checksums.
Retain the preceding release for rollback and preserve existing AUZiX downloads.

This is a preview. The signed public repository is live. The target Flatpak
query was corrected in installer r6; a disposable installation and its boot to
the installed login greeter passed. Preserved-home reinstall, authenticated
installed-desktop login and physical hardware remain separate acceptance work.
Media availability is shown on the public page only after publication succeeds.
