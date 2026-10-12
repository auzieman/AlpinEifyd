#!/usr/bin/python3
"""E'ifyd: graphical, console and saved-plan access to native Alpine installation."""
import argparse
from contextlib import contextmanager
import fcntl
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import eifyd_storage as storage

run = storage.run
disks = storage.disks
children = storage.children


def target_flatpak(destination, *args):
    # Flatpak supports an alternate system installation directly. A bare target
    # chroot has no /proc boot_id and cannot open the OSTree repository.
    env = os.environ.copy()
    env['FLATPAK_SYSTEM_DIR'] = str(destination)
    return run('flatpak', *args, env=env, stdout=subprocess.PIPE, text=True)


@contextmanager
def workspace():
    work = Path(tempfile.mkdtemp(prefix='eifyd-'))
    try:
        yield work
    finally:
        # Never let temporary-directory cleanup recurse into a target that failed
        # to unmount. Keep the working directory for explicit recovery instead.
        mounted = any(line.split()[4].startswith(str(work) + '/')
                      for line in Path('/proc/self/mountinfo').read_text().splitlines())
        if mounted:
            print('Target is still mounted; retained workspace: ' + str(work), flush=True)
        else:
            shutil.rmtree(work)

def configure_overlay(root, plan, password_hash, source=Path('/')):
    etc = root / 'etc'
    user = plan['username']
    passwd = (etc / 'passwd').read_text().splitlines()
    if any(line.split(':')[0] == user for line in passwd):
        raise ValueError('That account name is already reserved on this system.')
    live = next((line.split(':') for line in passwd if line.startswith('alpine:')), None)
    if not live:
        raise ValueError('Expected AlpinE live account is absent; refusing to guess account IDs.')
    uid, gid = live[2:4]
    passwd = [line for line in passwd if not line.startswith('alpine:')]
    passwd.append(f'{user}:x:{uid}:{gid}:{user}:/home/{user}:/bin/ash')
    (etc / 'passwd').write_text('\n'.join(passwd) + '\n')
    shadow = []
    for line in (etc / 'shadow').read_text().splitlines():
        fields = line.split(':')
        if fields[0] == 'alpine':
            continue
        if fields[0] == 'root':
            fields[1] = '!'
        shadow.append(':'.join(fields))
    shadow.append(f'{user}:{password_hash}:{int(time.time() // 86400)}:0:99999:7:::')
    (etc / 'shadow').write_text('\n'.join(shadow) + '\n')
    (etc / 'shadow').chmod(0o600)
    groups = []
    for line in (etc / 'group').read_text().splitlines():
        fields = line.split(':')
        if fields[0] == 'alpine':
            fields[0] = user
        fields[3] = ','.join(user if m == 'alpine' else m for m in fields[3].split(','))
        groups.append(':'.join(fields))
    (etc / 'group').write_text('\n'.join(groups) + '\n')
    for path in ('sudoers.d/alpine-live', 'doas.d/live.conf', 'machine-id'):
        (etc / path).unlink(missing_ok=True)
    for path in (etc / 'ssh').glob('ssh_host_*'):
        path.unlink()
    for path in (etc / 'lightdm').rglob('*.conf'):
        path.write_text('\n'.join(line for line in path.read_text().splitlines()
                                  if not line.strip().startswith('autologin-')) + '\n')
    (etc / 'sudoers.d').mkdir(exist_ok=True)
    rule = etc / 'sudoers.d/eifyd-wheel'
    rule.write_text('%wheel ALL=(ALL:ALL) ALL\n')
    rule.chmod(0o440)
    (etc / 'hostname').write_text(plan['hostname'] + '\n')
    (etc / 'timezone').write_text(plan['timezone'] + '\n')
    (etc / 'localtime').unlink(missing_ok=True)
    shutil.copyfile(source / 'usr/share/zoneinfo' / plan['timezone'], etc / 'localtime')
    home = root / 'home' / user
    shutil.rmtree(root / 'home/alpine', ignore_errors=True)
    shutil.rmtree(root / 'root/.ssh', ignore_errors=True)
    shutil.copytree(etc / 'skel', home, symlinks=True)
    for parent, dirs, files in os.walk(home):
        os.chown(parent, int(uid), int(gid))
        for name in dirs + files:
            os.chown(Path(parent) / name, int(uid), int(gid), follow_symlinks=False)
    # These image-owned helpers are outside APK; native package files stay APK-owned.
    shutil.copytree(source / 'usr/local', root / 'usr/local', symlinks=True, dirs_exist_ok=True)



def selected_world(plan, world):
    optional = set(storage.choices('apk'))
    selected = set(plan['apk'])
    return [p for p in world if re.split(r'[<>=~@]', p, maxsplit=1)[0] not in optional or
            re.split(r'[<>=~@]', p, maxsplit=1)[0] in selected]


def inspect_home(receipt, work, uid, gid):
    """Read existing home without journal replay, before formatting anything."""
    row = next(r for r in receipt['partitions'] if r['mount'] == '/home')
    if row['format']:
        return
    probe = work / 'home-check'
    probe.mkdir()
    run('mount', '-t', 'ext4', '-o', 'ro,noload', row['device'], str(probe))
    try:
        home = probe / receipt['plan']['username']
        if home.is_symlink():
            raise ValueError('Existing user home is a symlink; choose another account.')
        if home.exists() and (not home.is_dir() or home.stat().st_uid != uid or home.stat().st_gid != gid):
            raise ValueError('Existing home ownership differs from the live account UID/GID; resolve ownership before installing.')
    finally:
        run('umount', str(probe))


def install(plan, token, password):
    if os.geteuid() != 0:
        raise ValueError('Installation requires administrator privileges.')
    receipt, current = storage.inspect(plan)
    if not token or token != current:
        raise ValueError('The plan or disk has changed. Review again before installing.')
    if not isinstance(password, str) or len(password) < 8 or '\n' in password or '\x00' in password:
        raise ValueError('Use a password of at least eight characters without newlines.')
    lock = open('/run/lock/eifyd-install.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise ValueError('Another installation is already running.')
    hashed = run('openssl', 'passwd', '-6', '-stdin', input=password + '\n',
                 text=True, capture_output=True).stdout.strip()
    del password
    plan = receipt['plan']
    with workspace() as work:
        overlay = work / 'overlay'
        overlay.mkdir()
        archive = work / 'desktop.apkovl.tar.gz'
        print('Preparing account, desktop defaults and package selection...', flush=True)
        run('lbu', 'package', str(archive))
        run('tar', '-xzf', str(archive), '-C', str(overlay))
        configure_overlay(overlay, plan, hashed)
        # Never extract defaults over a preserved home. Seed only an absent home later.
        seed = work / 'home-seed'
        shutil.move(str(overlay / 'home' / plan['username']), seed)
        shutil.rmtree(overlay / 'home', ignore_errors=True)
        account = next(x.split(':') for x in (overlay / 'etc/passwd').read_text().splitlines()
                       if x.startswith(plan['username'] + ':'))
        uid, gid = int(account[2]), int(account[3])
        world = overlay / 'etc/apk/world'
        world.write_text('\n'.join(selected_world(plan, world.read_text().splitlines())) + '\n')
        # Do not clone the live machine's stale partition map.
        (overlay / 'etc/fstab').unlink(missing_ok=True)
        run('tar', '-czf', str(archive), '-C', str(overlay), '.')
        inspect_home(receipt, work, uid, gid)
        if plan['flatpak']:
            available = run('flatpak', 'list', '--system', '--app', '--columns=application',
                            capture_output=True, text=True).stdout.split()
            missing = set(plan['flatpak']) - set(available)
            for app in sorted(missing):
                # Resolve online choices before touching the destination disk.
                run('flatpak', 'remote-info', '--system', 'flathub', app)
        # Resolve the selected native closure before any destructive operation.
        print('Checking signed repositories and package dependencies...', flush=True)
        run('apk', 'update')
        run('apk', 'add', '--simulate', *world.read_text().splitlines(), 'linux-lts', 'grub',
            'grub-efi' if receipt['firmware'] == 'uefi' else 'grub-bios')
        if storage.inspect(plan)[1] != token:
            raise ValueError('Disk changed during preparation; review again.')
        mounted_root = work / 'target'
        mounted_root.mkdir()
        mounted = storage.prepare(receipt, mounted_root)
        try:
            print('Installing native Alpine packages and GRUB...', flush=True)
            env = os.environ.copy()
            # Native setup-disk detects firmware; inspect() already checked the requested mode.
            env['BOOTLOADER'] = 'grub'
            run('setup-disk', '-m', 'sys', '-B', 'grub', '-b', plan['disk'], '-s', '0',
                '-k', 'lts', '-o', str(archive), str(mounted_root), env=env)
            if (mounted_root / 'etc/hostname').read_text().strip() != plan['hostname']:
                raise ValueError('Installed target does not match the account plan.')
            home = mounted_root / 'home' / plan['username']
            if not home.exists():
                shutil.copytree(seed, home, symlinks=True)
                for parent, dirs, files in os.walk(home):
                    os.chown(parent, uid, gid)
                    for name in dirs + files:
                        os.chown(Path(parent) / name, uid, gid, follow_symlinks=False)
            if plan['flatpak']:
                destination = mounted_root / 'var/lib/flatpak'
                destination.mkdir(parents=True, exist_ok=True)
                if Path('/var/lib/flatpak').is_dir():
                    print('Reusing live Flatpak data...', flush=True)
                    run('rsync', '-aHAX', '--info=progress2', '/var/lib/flatpak/', str(destination) + '/')
                target_flatpak(destination, 'remote-add', '--system', '--if-not-exists',
                               'flathub', 'https://flathub.org/repo/flathub.flatpakrepo')
                installed = target_flatpak(destination, 'list', '--system',
                                           '--app', '--columns=application').stdout.split()
                remove = sorted(set(installed) - set(plan['flatpak']))
                if remove:
                    result = target_flatpak(destination, 'uninstall', '--system',
                                            '--noninteractive', '-y', *remove)
                    print(result.stdout, flush=True)
                    installed = target_flatpak(destination, 'list', '--system',
                                               '--app', '--columns=application').stdout.split()
                missing = set(plan['flatpak']) - set(installed)
                for app in sorted(missing):
                    print('Installing target Flatpak: ' + app, flush=True)
                    result = target_flatpak(destination, 'install', '--system',
                                            '--noninteractive', '-y', 'flathub', app)
                    print(result.stdout, flush=True)
                installed = target_flatpak(destination, 'list', '--system',
                                           '--app', '--columns=application').stdout.split()
                if set(plan['flatpak']) - set(installed):
                    raise ValueError('Target Flatpak installation is incomplete.')
            # Retain a password-free receipt in the installed system.
            receipt_dir = mounted_root / 'var/lib/eifyd'
            receipt_dir.mkdir(parents=True, exist_ok=True)
            (receipt_dir / 'installation.json').write_text(json.dumps(receipt, indent=2) + '\n')
            run('sync')
            print('System installed. Finishing mounts...', flush=True)
        finally:
            storage.unmount(mounted)
    print('COMPLETE: shut down, remove the live media, and boot the installed disk.', flush=True)


def review(plan):
    receipt, token = storage.inspect(plan)
    print('REVIEW_ID=' + token)
    print(storage.describe(receipt))
    return receipt, token


def tui():
    print("GET E’IFYD — console installation")
    for disk in disks():
        if disk['type'] == 'disk':
            print(f"{disk['path']}: {int(disk['size']) / storage.GIB:.1f} GiB"
                  + (' [in use]' if storage.in_use(disk) else ''))
    disk = input('Target disk (blank cancels): ').strip()
    if not disk:
        return
    plan = dict(disk=disk, hostname=input('Computer name [alpine-workstation]: ').strip() or 'alpine-workstation',
                username=input('Account name: ').strip(),
                timezone=input('Timezone [UTC]: ').strip() or 'UTC')
    plan['mode'] = 'existing' if input('Use existing partitions? [y/N]: ').lower() == 'y' else 'new'
    if plan['mode'] == 'new':
        plan['root_gib'] = int(input('Root size in GiB [48]: ') or '48')
    else:
        for key, title in [('root', 'Root (will format)'), ('home', 'Home'),
                           ('boot_partition', 'Boot (optional)'), ('esp', 'EFI (UEFI only)')]:
            plan[key] = input(title + ' partition: ').strip()
        plan['format_home'] = input('Format home, erasing its files? [y/N]: ').lower() == 'y'
        plan['format_boot'] = input('Format selected boot partition? [y/N]: ').lower() == 'y'
    plan['apk'], plan['flatpak'] = [], []
    for group in storage.catalog():
        if input('Include ' + group['name'] + '? [Y/n]: ').lower() != 'n':
            plan['apk'] += group['apk']
            plan['flatpak'] += group['flatpak']
    receipt, token = review(plan)
    action = input('[s] Save plan, [i] Install reviewed plan, [Enter] Cancel: ').lower()
    if action == 's':
        with open(input('New plan filename: ').strip(), 'x') as output:
            json.dump(receipt['plan'], output, indent=2)
            output.write('\n')
        print('Saved. No disk changes made.')
    elif action == 'i':
        password = getpass.getpass('Password: ')
        if password != getpass.getpass('Repeat password: '):
            raise ValueError('Passwords do not match.')
        install(receipt['plan'], token, password)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inventory', 'catalog', 'review', 'install', 'tui'])
    parser.add_argument('--plan', help='Saved JSON plan; otherwise read a JSON request from stdin')
    parser.add_argument('--accept-plan', help='Exact review ID for unattended installation')
    parser.add_argument('--password-fd', type=int, help='Read unattended password from this inherited descriptor')
    args = parser.parse_args()
    if args.action == 'inventory':
        print(f"INFO\t{storage.minimum_root()}\t" +
              ('uefi' if Path('/sys/firmware/efi').exists() else 'bios'))
        for disk in disks():
            if disk['type'] != 'disk':
                continue
            for node in children(disk):
                if node['type'] not in ('disk', 'part'):
                    continue
                label = f"{node['path']} — {int(node['size']) / storage.GIB:.1f} GiB " + (node.get('fstype') or node.get('model') or '')
                if storage.in_use(disk):
                    label += ' [in use]'
                print('\t'.join([node['type'], node['path'], disk['path'], str(node['size']),
                                 label.replace('\t', ' ').replace('\n', ' ')]))
        return
    if args.action == 'catalog':
        for group in storage.catalog():
            for kind in ('apk', 'flatpak'):
                for package in group[kind]:
                    print('\t'.join([group['name'], kind, package]))
        return
    if args.action == 'tui':
        tui()
        return
    request = dict(plan=json.loads(Path(args.plan).read_text())) if args.plan else json.load(sys.stdin)
    if not isinstance(request, dict) or set(request) - {'plan', 'token', 'password'}:
        raise ValueError('Invalid request.')
    plan = storage.normalize(request.get('plan'))
    if args.action == 'review':
        review(plan)
    else:
        password = request.get('password', '')
        if args.password_fd is not None:
            with os.fdopen(args.password_fd) as stream:
                password = stream.readline().rstrip('\n')
        install(plan, args.accept_plan or request.get('token'), password)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, RuntimeError, OSError, EOFError, KeyboardInterrupt, subprocess.CalledProcessError) as error:
        print('ERROR: ' + (str(error) or 'Cancelled.'), file=sys.stderr, flush=True)
        raise SystemExit(1)
