#!/bin/sh
set -eu
# Native alpine-make-vm-image runs this hook inside the target root.
printf '%s\n' '[configure] Registering udev for boot (not starting it in chroot)'
# Same runlevels as setup-devd's enable_udev; daemon startup belongs to boot.
for service in mdev hwdrivers; do
    if [ -L "/etc/runlevels/sysinit/$service" ]; then
        rc-update del "$service" sysinit
    fi
done
for service in udev udev-trigger udev-settle; do rc-update add "$service" sysinit; done
rc-update add udev-postmount default
printf '%s\n' '[configure] Registering networking and desktop services'
if [ -L /etc/runlevels/boot/networking ]; then rc-update del networking boot; fi
printf 'auto lo\niface lo inet loopback\n' > /etc/network/interfaces
rc-update add networkmanager default
rc-update add bluetooth default
rc-update add dbus default
rc-update add elogind boot
rc-update add lightdm default
printf '%s\n' '[configure] Creating local live-media user'
adduser -D -s /bin/ash alpine
for group in audio video input netdev wheel; do addgroup alpine "$group"; done
passwd -d alpine
passwd -d root
mkdir -p /etc/doas.d
printf 'permit nopass alpine as root\n' > /etc/doas.d/live.conf
chmod 0600 /etc/doas.d/live.conf
mkdir -p /etc/sudoers.d
printf 'alpine ALL=(ALL:ALL) NOPASSWD: ALL\n' > /etc/sudoers.d/alpine-live
chmod 0440 /etc/sudoers.d/alpine-live
visudo -c
npm install --global @openai/codex@0.155.1
codex --version
printf '\nautologin-user=alpine\nautologin-user-timeout=0\n' >> /etc/lightdm/lightdm.conf.d/50-alpine.conf
# Local live-media accounts only; no SSH server is enabled.
printf '%s\n' '[configure] Checking desktop session, package selection and service links'
test -f /usr/share/xsessions/enlightenment.desktop
for service in udev udev-trigger udev-settle; do
    test -x "/etc/runlevels/sysinit/$service"
done
for service in dbus lightdm udev-postmount networkmanager bluetooth; do test -x "/etc/runlevels/default/$service"; done
test -x /etc/runlevels/boot/elogind
test -f /home/alpine/.xinitrc
apk info -e enlightenment terminology e-theme-dark e-theme-transient e-theme-transient-color alpine-spin-wallpapers
apk info -e sudo networkmanager blueman pipewire wireplumber firefox libreoffice flatpak
test -f /usr/share/enlightenment/data/config/standard/e.cfg
test -f /etc/xdg/autostart/pipewire.desktop
apk info -v > /etc/alpine-spin/packages-built.txt
printf '%s\n' 'AlpinE image configuration complete' > /etc/alpine-spin/configure.complete
printf '%s\n' '[configure] COMPLETE'
