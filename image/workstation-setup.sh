#!/bin/sh
set -eu
flatpak remote-add --system --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
failed=0
while IFS= read -r app; do
    printf '\n[workstation] Installing %s\n' "$app"
    flatpak install --system --noninteractive -y flathub "$app" || failed=1
done < /etc/alpine-spin/workstation-flatpaks
npm install --global @openai/codex@0.155.1 || failed=1
codex --version || failed=1
flatpak list --app --columns=application,version
exit "$failed"
