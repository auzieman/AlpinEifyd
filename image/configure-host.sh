#!/bin/sh
set -eu
# alpine-make-vm-image invokes this hook with the mounted target as cwd.
# Configure native services inside it; Flatpak's sandbox must start outside
# chroot so Linux permits the user namespace used by extra-data installers.
image_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target=$(pwd -P)
test -f "$target/etc/alpine-release"
chroot "$target" /bin/sh < "$image_dir/configure.sh"
export FLATPAK_SYSTEM_DIR="$target/var/lib/flatpak"
flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
failed=0
while IFS= read -r app; do
    printf '\n[workstation] Installing %s\n' "$app"
    flatpak install --system --noninteractive -y flathub "$app" || failed=1
done < "$target/etc/alpine-spin/workstation-flatpaks"
flatpak list --system --app --columns=application,version
test "$failed" = 0
printf '%s\n' '[configure-host] Removing image-only download caches'
chroot "$target" npm cache clean --force
flatpak uninstall --system --unused --noninteractive -y
df -h "$target"
cp "$target/etc/alpine-spin/configure.complete" "$image_dir/configure.complete"
printf '%s\n' '[configure-host] COMPLETE'
