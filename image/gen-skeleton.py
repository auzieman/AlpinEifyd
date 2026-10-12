#!/usr/bin/env python3
"""Create the filesystem skeleton consumed by alpine-make-vm-image."""
import os
from pathlib import Path
import re
import shlex
import sys
from urllib.parse import urlparse

image = Path(__file__).resolve().parent
# This is a public system skeleton, even when the caller protects private state
# with umask 077. Individual sensitive files must specify their own modes.
os.umask(0o022)
hostname = sys.argv[1]
if not re.fullmatch(r'[a-z0-9-]+', hostname):
    raise SystemExit('Invalid live hostname')
repo = os.environ.get('ALPINE_REPOSITORY_URL', 'https://auzix.auzietek.com/alpine/repo/v3.24')
url = urlparse(repo)
if url.scheme not in ('https', 'http') or not url.hostname or url.username or any(c.isspace() for c in repo):
    raise SystemExit('Supply a reachable HTTP(S) AlpinE repository URL')
key = Path(os.environ['ALPINE_REPOSITORY_KEY'])
if not key.name.endswith('.rsa.pub') or b'PRIVATE KEY' in key.read_bytes():
    raise SystemExit('Supply only the APK repository public .rsa.pub key')
repositories = ['https://dl-cdn.alpinelinux.org/alpine/v3.24/main',
                'https://dl-cdn.alpinelinux.org/alpine/v3.24/community', repo]
root = Path(sys.argv[2])
root.mkdir(parents=True, exist_ok=False)
def write(name, content, mode=0o644):
    path = root/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    path.chmod(mode)
write('etc/hostname', hostname+'\n')
write('etc/alpine-spin/workstation-flatpaks', (image/'workstation-flatpaks').read_text())
write('usr/local/lib/alpine-spin/workstation-setup.sh',
      (image/'workstation-setup.sh').read_text(), 0o755)
write('etc/apk/repositories', '\n'.join(repositories)+'\n')
write('etc/apk/keys/'+key.name, key.read_text())
write('etc/issue', "AlpinE by Auzietek — Alpine Linux 3.24\nGet E'ifyd: log in as root, then run setup-eifyd.\n\n")
write('etc/motd', "Welcome to AlpinE. Native Alpine tools and repositories remain available.\nOpen Get E'ifyd on the desktop, or run setup-eifyd --help.\n")
write('etc/alpine-spin/answers', 'APKREPOSOPTS='+shlex.quote(' '.join(repositories))+'\nDEVDOPTS=udev\n')
write('usr/local/sbin/setup-eifyd',
      '#!/bin/sh\nset -eu\nprintf "%s\\n" "Get E\047ifyd — install AlpinE (Alpine Linux)"\n'
      'if [ "$#" -eq 0 ]; then set -- --help; fi\n'
      'exec /usr/libexec/eifyd-install "$@"\n', 0o755)
write('etc/skel/.xinitrc', '#!/bin/sh\nexec enlightenment_start\n', 0o755)
write('usr/local/bin/laptop-panel-fallback',
      '#!/bin/sh\n'
      '# Keep the laptop panel at 0,0 whenever HDMI-1 is not connected.\n'
      'fold_to_panel() {\n'
      '  state=$(xrandr --query 2>/dev/null) || return 0\n'
      '  printf "%s\\n" "$state" | grep -q "^HDMI-1 connected" && return 0\n'
      '  printf "%s\\n" "$state" | grep -q "^eDP-1 connected" || return 0\n'
      '  xrandr --output HDMI-1 --off --output eDP-1 --primary --mode 1600x900 --pos 0x0\n'
      '}\n'
      'fold_to_panel\n'
      'while true; do\n'
      '  sleep 2\n'
      '  fold_to_panel\n'
      'done\n', 0o755)
write('etc/xdg/autostart/laptop-panel-fallback.desktop',
      '[Desktop Entry]\nType=Application\nName=Laptop panel fallback\n'
      'Exec=/usr/local/bin/laptop-panel-fallback\n'
      'X-GNOME-Autostart-enabled=true\n')
write('etc/skel/.e/e/applications/startup/.order',
      '/etc/xdg/autostart/pipewire.desktop\n'
      '/etc/xdg/autostart/nm-applet.desktop\n'
      '/etc/xdg/autostart/blueman.desktop\n'
      '/etc/xdg/autostart/laptop-panel-fallback.desktop\n')
# The standard Enlightenment profile already enables its native polkit agent.
write('etc/environment', 'LANG=en_US.UTF-8\nXDG_CURRENT_DESKTOP=Enlightenment\n')
write('etc/profile.d/alpine-desktop.sh',
      'export LANG=en_US.UTF-8\nexport TERMINAL=terminology\n'
      'export E_CONF_PROFILE=standard\n')
write('etc/skel/.xsession',
      '#!/bin/sh\nexport E_CONF_PROFILE=standard\nexport LANG=en_US.UTF-8\n'
      'export XDG_CURRENT_DESKTOP=Enlightenment\nexport TERMINAL=terminology\n'
      'exec enlightenment_start\n', 0o755)
write('etc/NetworkManager/NetworkManager.conf',
      '[main]\nplugins=keyfile\n[ifupdown]\nmanaged=true\n')
write('etc/xdg/xdg-desktop-portal/portals.conf', '[preferred]\ndefault=gtk\n')
write('usr/share/applications/alpine-codex.desktop',
      '[Desktop Entry]\nType=Application\nName=Codex Terminal\n'
      'Exec=terminology -e codex\nIcon=utilities-terminal\n'
      'Categories=Development;\nTerminal=false\n')
write('etc/skel/.config/mimeapps.list',
      '[Default Applications]\ntext/html=firefox.desktop\n'
      'x-scheme-handler/http=firefox.desktop\nx-scheme-handler/https=firefox.desktop\n'
      'text/plain=org.xfce.mousepad.desktop\n')
write('etc/lightdm/lightdm.conf.d/50-alpine.conf',
      '[Seat:*]\nuser-session=enlightenment\ngreeter-session=lightdm-gtk-greeter\n')
write('etc/lightdm/lightdm-gtk-greeter.conf',
      '[greeter]\nbackground=/usr/share/backgrounds/alpine/alpine-midnight.svg\n')
write('etc/lbu/include', '/usr/local/sbin/setup-eifyd\n')
# The installer APK owns its application entry and /etc/skel/Desktop shortcut.
write('usr/local/bin/alpine-packages',
      '#!/bin/sh\nprintf "%s\\n" "AlpinE packages — native APK" '
      '"Search: apk search NAME" "Install: doas apk add NAME" '
      '"Remove: doas apk del NAME" "Update: doas apk update && doas apk upgrade"\n'
      'exec /bin/ash -i\n', 0o755)
write('usr/share/applications/alpine-packages.desktop',
      '[Desktop Entry]\nType=Application\nName=Packages (APK console)\n'
      'Comment=Search and manage native Alpine packages\n'
      'Exec=terminology -e /usr/local/bin/alpine-packages\n'
      'Icon=/usr/share/eifyd/mark-shield-swords.png\nCategories=System;\nTerminal=false\n')
for name in ['alpine-packages.desktop']:
    write('etc/skel/Desktop/'+name, (root/'usr/share/applications'/name).read_text(), 0o755)
