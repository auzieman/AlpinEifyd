# Gaming and Amiga desktop

The requested daily-driver selection adds Bottles, Steam with Proton and FS-UAE
with its launcher. profiles/gaming-retro.json extends the workstation profile;
the minimal E image remains small. These are selections, not installed or tested
applications yet.

Bottles: use its supported Flatpak distribution. Steam: use Alpine's documented
Flatpak route. Select and test a Proton/runtime combination on the actual Alpine
host; do not assume every Steam-downloaded Proton works on musl just because
the client opens. Exact runtime versions remain unpinned until release selection.

FS-UAE and fs-uae-launcher: prefer native Alpine packages where provided by our
selected release; the existing Flathub application is a fallback. User Amiga
ROMs, disk images and saved configurations remain user data, separate from the
distribution and package repository.

Desktop acceptance: E/X11 menu launchers, Flatpak portal/file-picker integration,
GPU rendering and applicable 32-bit Vulkan/OpenGL runtime support, sound,
controller input, a real Proton game, a Bottles application and FS-UAE boot with
the user's media. Keep app state and game libraries persistent across updates.
Validate hardware drivers on the intended desktop rather than inferring them
from successful VM or CLI tests.

References checked 2026-09-19:
- https://usebottles.com/docs/getting-started/installation.md
- https://wiki.alpinelinux.org/wiki/Steam
- https://wiki.alpinelinux.org/wiki/Flatpak
- https://github.com/ValveSoftware/Proton
- https://pkgs.alpinelinux.org/packages?name=fs-uae*&branch=edge&arch=x86_64
- https://flathub.org/apps/net.fsuae.FS-UAE
- https://fs-uae.net/download/linux/
