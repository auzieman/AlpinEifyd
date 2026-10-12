# Native companion APKs — AlpinE 3.24 x86_64

Packages: **ejamz 0.1.0-r0** and **blackknight-wallpapers 0.1.0-r0**.

This separately signed companion feed sits alongside the existing signed AlpinE
feed and matching Alpine 3.24 main/community repositories. The existing feed
and its signing identity remain unchanged. These instructions assume that
normal AlpinE 3.24 repository/key setup is already present; do not mix edge or
other Alpine releases.

## Install

Verify the downloaded public key against the fingerprint published here before
adding it to APK’s trusted keys. This new key is required for the companion feed.
No unsigned-repository bypass is used.

```sh
wget -O /tmp/builder-6acd560b.rsa.pub https://auzix.auzietek.com/alpine/repo/apps/v3.24/builder-6acd560b.rsa.pub
printf '%s\n' 'f308145bc1a64270e85f58d8af810015a5e2605a5bba1ddbeb2f86da65a42bd4  /tmp/builder-6acd560b.rsa.pub' | sha256sum -c -
sudo install -m 0644 /tmp/builder-6acd560b.rsa.pub /etc/apk/keys/builder-6acd560b.rsa.pub
grep -qxF 'https://auzix.auzietek.com/alpine/repo/apps/v3.24' /etc/apk/repositories || printf '%s\n' 'https://auzix.auzietek.com/alpine/repo/apps/v3.24' | sudo tee -a /etc/apk/repositories
sudo apk update
sudo apk add ejamz blackknight-wallpapers
```

Public key: [builder-6acd560b.rsa.pub](../keys/builder-6acd560b.rsa.pub). SHA256: `f308145bc1a64270e85f58d8af810015a5e2605a5bba1ddbeb2f86da65a42bd4`.

Launch **E-Jamz** from the menu or run `ejamz`. Its packaged launcher selects the
installed Edje skin independently of the current working directory and passes
file/folder arguments to the player. It preserves user settings under the normal
XDG configuration directory. GStreamer plugins and FFmpeg are runtime dependencies.

Choose BlackKnight Storm or Still from Enlightenment’s wallpaper settings. The
package places both under `/usr/share/enlightenment/data/backgrounds`; it does
not switch an existing desktop’s theme or wallpaper. The full Sci-Fi donor-derived
desktop theme is excluded pending upstream redistribution verification.

## Source and notices

- E-Jamz source commit: `7171240207e3a39de2afa1329ec9f7579c52cf78` ([v0.1.0](https://github.com/auzieman/E-Jamz/tree/v0.1.0)).
- BlackKnight source commit: `d6f035908ff0719e4fcd8e644001aca7e9424b32` ([v0.1.0](https://github.com/auzieman/BlackKnight-E-Theme/tree/v0.1.0)).
- [E-Jamz APKBUILD](../aports/ejamz/APKBUILD), [wallpaper APKBUILD](../aports/blackknight-wallpapers/APKBUILD): archive SHA512 checksums, runtime dependencies and native build commands.

Original code is GPL-3.0-only; original artwork is CC-BY-SA-4.0; Doto retains OFL-1.1.
Notices and licenses remain in each installed package under `/usr/share/doc`.
The private signing key is retained only on the build host, outside source and
public web directories.

## Acceptance and rollback

Package-build evidence is recorded separately from retained interactive v0.1.0
playback and desktop acceptance. No host installation, image rebuild or new
physical-hardware validation is claimed by this package publication.

Public feed snapshots are immutable and the preceding pointer is retained for
rollback. To remove only these applications, use `sudo apk del ejamz
blackknight-wallpapers`; this does not remove user music or settings. Removing
the companion repository line is a separate configuration change.

Package acceptance: BKC run `490909fd-80e2-4c31-aa0a-c38dfbdac8b8` completed. Signed APK verification, clean-root installation (including GStreamer/FFmpeg dependencies), installed launcher/skin/wallpaper presence and musl ELF linkage passed. Compiler image: `sha256:95b932cbd2899218225a6783074acfba1cd26abae142f1ec26ba8f13c3c83f8f`. [Published byte manifest](https://auzix.auzietek.com/alpine/repo/apps/v3.24/manifest.json) records APK/index/key hashes. The packages were built in run 0fec78a6-2f99-41cf-9fcc-394e3c769883; the final validation run reused those signed packages after exact recipe-hash comparison.

Publication run `cc54ba45-4cdb-4c97-9c05-4400a4e34984` completed. HTTPS byte checks and a fresh Alpine client’s signature/key checks and package resolution passed. [Release article](https://beta.auzietek.com/post/alpine-native-companion-apps-e-jamz-blackknight?lane=auzietek).
