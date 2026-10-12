# Initial native package run

Base: Alpine 3.24.2 x86_64, pinned OCI platform manifest in Dockerfile.
Only v3.24 official repositories supply ordinary build dependencies.

EFL 1.28.1 and Enlightenment 0.27.1 recovered from the proven AUZiX source-intake
desktop recipes (auzix_rethink/docker/source-intake/desktop). Those copies already
use standard abuild-meson paths. EFL retains its three localized source fixes:
disable exactness, correct the Elementary callback signature, rename Embryo's
constexpr identifier. Added prepare.py to the checked source list and declared
Python as its build dependency. Enlightenment retains X11-only settings and
upstream suid helper declaration; its cached source checksum is now explicit.
This recovers prior successful logic; it is not yet proof on the newer compiler.

Terminology 1.14.0 recipe and test patch copied unchanged from Alpine aports:
https://github.com/alpinelinux/aports/tree/4f2ade3df4a1e4ff0f68458076098c7a716c45a9/testing/terminology

build/order selects the three origins. Native abuild owns source verification,
compile, subpackages, hooks, dependency discovery, signing and indexing. External
build/check dependencies are resolved from these recipes into the compiler image
first. Internal efl-dev comes from the freshly built local repository.
Persistent distfiles and APK outputs remain outside Git. Work directories are
keyed by the Docker compiler image ID; only that identical input image may reuse
the completion markers. No AUZiX path rewrite or alternate loader is applied.

## Native companion APKs — 2026-10-12

E-Jamz and BlackKnight wallpaper recipes pin the original v0.1.0 commits and codeload SHA512 checksums. BKC run `490909fd-80e2-4c31-aa0a-c38dfbdac8b8` validates the signed packages built in 0fec78a6-2f99-41cf-9fcc-394e3c769883 after exact recipe-hash comparison. Compiler image `sha256:95b932cbd2899218225a6783074acfba1cd26abae142f1ec26ba8f13c3c83f8f` derives from the pinned Alpine 3.24.2 base with matching signed AlpinE EFL dependencies. Installed GStreamer/FFmpeg dependencies and musl linkage were verified in a clean root. Wallpaper EDJs match the accepted release bytes; interactive acceptance remains separately retained. Source recipe and public byte hashes are in docs/companion-apk-evidence.json.
