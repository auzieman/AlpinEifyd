"""Installation plans and native disk operations shared by all E'ifyd frontends."""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

GIB = 1024**3
BIOS_GUID = '21686148-6449-6e6f-744e-656564454649'
EFI_GUID = 'c12a7328-f81f-11d2-ba4b-00a0c93ec93b'


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def catalog():
    path = Path(__file__).with_name('package-groups.json')
    return json.loads(path.read_text())


def choices(kind):
    return sorted({p for group in catalog() for p in group[kind]})


def disks():
    return json.loads(run('lsblk', '-J', '-b', '--tree', '-o',
                         'PATH,TYPE,SIZE,FSTYPE,MOUNTPOINTS,MODEL,SERIAL,WWN,RO,PTTYPE,PARTTYPE,UUID',
                         capture_output=True, text=True).stdout)['blockdevices']


def children(node):
    yield node
    for child in node.get('children', []):
        yield from children(child)


def in_use(disk):
    return any(any(n.get('mountpoints') or []) or n.get('ro') or
               n['type'] not in ('disk', 'part') for n in children(disk))


def minimum_root():
    return max(24, math.ceil(shutil.disk_usage('/').used / GIB) + 8)


def firmware_mode():
    return 'uefi' if Path('/sys/firmware/efi').exists() else 'bios'


def normalize(data):
    if not isinstance(data, dict):
        raise ValueError('An installation plan must be an object.')
    defaults = dict(format='eifyd-install-v2', mode='new', boot='auto', root_gib=48,
                    root='', home='', esp='', boot_partition='', format_home=False,
                    format_boot=False, format_root=True, hostname='alpine-workstation',
                    username='', timezone='UTC', disk='', apk=choices('apk'),
                    flatpak=choices('flatpak'))
    if set(data) - set(defaults):
        raise ValueError('Unsupported installation plan fields: ' + ', '.join(sorted(set(data)-set(defaults))))
    plan = defaults | data
    if plan['format'] != 'eifyd-install-v2':
        raise ValueError('Expected eifyd-install-v2; review old plans in the new installer.')
    for key in ('disk', 'root', 'home', 'esp', 'boot_partition'):
        if not isinstance(plan[key], str) or (plan[key] and not re.fullmatch(r'/dev/[A-Za-z0-9_-]+', plan[key])):
            raise ValueError('Invalid device for ' + key)
    for key in ('hostname', 'username'):
        if not isinstance(plan[key], str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,30}', plan[key]):
            raise ValueError(key + ': use a lowercase name beginning with a letter.')
    if plan['username'] in ('root', 'alpine'):
        raise ValueError('Choose an account name other than root or the live account alpine.')
    zone = plan['timezone']
    if not isinstance(zone, str) or not re.fullmatch(r'[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+)*', zone) or not (Path('/usr/share/zoneinfo') / zone).is_file():
        raise ValueError('Choose an installed timezone, for example America/Los_Angeles.')
    if plan['mode'] not in ('new', 'existing') or plan['boot'] not in ('auto', 'bios', 'uefi'):
        raise ValueError('Unsupported layout or firmware mode.')
    if type(plan['root_gib']) is not int or not 24 <= plan['root_gib'] <= 1048576:
        raise ValueError('Root size must be a whole number of GiB, at least 24.')
    for key in ('format_root', 'format_home', 'format_boot'):
        if type(plan[key]) is not bool:
            raise ValueError(key + ' must be true or false.')
    for kind in ('apk', 'flatpak'):
        values = plan[kind]
        if not isinstance(values, list) or not all(isinstance(p, str) for p in values) or set(values) - set(choices(kind)):
            raise ValueError('Unknown ' + kind + ' selection.')
        plan[kind] = sorted(set(values))
    return plan


def inspect(plan):
    plan = normalize(plan)
    disk = next((d for d in disks() if d['path'] == plan['disk']), None)
    if not disk or disk['type'] != 'disk':
        raise ValueError('Select a target disk.')
    if in_use(disk):
        raise ValueError('Target is in use, read-only, or contains active swap/volume mappings.')
    firmware = firmware_mode()
    boot = firmware if plan['boot'] == 'auto' else plan['boot']
    # setup-disk detects EFI itself; never silently produce a different boot mode.
    if boot != firmware:
        raise ValueError('Boot the live media in ' + boot.upper() + ' mode to install in that mode.')
    rows = []
    if plan['mode'] == 'new':
        if any(plan[k] for k in ('root', 'home', 'esp', 'boot_partition')):
            raise ValueError('Existing partition choices must be empty for a new layout.')
        if plan['root_gib'] < minimum_root() or int(disk['size']) < (plan['root_gib'] + 10) * GIB:
            raise ValueError(f'Root needs at least {minimum_root()} GiB; leave at least 10 GiB for boot and home.')
        for number, mount, fs in ((1, '/boot/efi' if boot == 'uefi' else 'BIOS boot',
                                    'vfat' if boot == 'uefi' else 'bios'),
                                  (2, '/boot', 'ext4'), (3, '/', 'ext4'), (4, '/home', 'ext4')):
            separator = 'p' if plan['disk'][-1].isdigit() else ''
            rows.append(dict(device=f"{plan['disk']}{separator}{number}", mount=mount,
                             filesystem=fs, format=fs != 'bios'))
    else:
        if not plan['root'] or not plan['format_root']:
            raise ValueError('Select a root partition and enable Format root for a clean installation.')
        if not plan['home']:
            raise ValueError('Select a separate home partition.')
        if boot == 'uefi' and not plan['esp']:
            raise ValueError('Select the existing EFI system partition; it will not be formatted.')
        if boot == 'bios' and plan['esp']:
            raise ValueError('EFI partition must be empty in BIOS mode.')
        parts = {n['path']: n for n in children(disk) if n['type'] == 'part'}
        specs = [('root', '/', True), ('home', '/home', plan['format_home']),
                 ('boot_partition', '/boot', plan['format_boot']), ('esp', '/boot/efi', False)]
        seen = set()
        for key, mount, fmt in specs:
            dev = plan[key]
            if not dev:
                continue
            part = parts.get(dev)
            if not part or dev in seen:
                raise ValueError('Partition choices must be distinct partitions on the target disk.')
            seen.add(dev)
            fs = 'vfat' if key == 'esp' else 'ext4'
            if not fmt and part.get('fstype') != fs:
                raise ValueError(f'{dev} must already contain {fs} to preserve it.')
            if key == 'esp' and (part.get('parttype') or '').lower() != EFI_GUID:
                raise ValueError('Selected EFI partition does not have the EFI system type.')
            if key == 'root' and int(part['size']) < minimum_root() * GIB:
                raise ValueError(f'Root partition needs at least {minimum_root()} GiB.')
            rows.append(dict(device=dev, mount=mount, filesystem=fs, format=fmt))
        if boot == 'bios' and disk.get('pttype') == 'gpt' and not any(
                (p.get('parttype') or '').lower() == BIOS_GUID for p in parts.values()):
            raise ValueError('BIOS GRUB on GPT needs an existing BIOS boot partition. Create it in GParted first.')
        if boot == 'bios' and disk.get('pttype') not in ('gpt', 'dos'):
            raise ValueError('Existing BIOS layout needs a GPT or DOS partition table.')
    # Bind confirmation to the actual devices, UUIDs and selected operations.
    fingerprint = [{k: n.get(k) for k in ('path', 'type', 'size', 'serial', 'wwn', 'uuid', 'parttype', 'pttype')}
                   for n in children(disk)]
    receipt = dict(plan=plan, firmware=boot, partitions=rows, identity=fingerprint)
    token = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
    return receipt, token


def describe(receipt):
    p = receipt['plan']
    lines = ["GET E’IFYD — Installation review", '',
             'Target: ' + p['disk'],
             ('ERASE the entire disk and create a new GPT layout.' if p['mode'] == 'new'
              else 'Keep the partition table; format only the partitions marked FORMAT.'), '']
    for row in receipt['partitions']:
        lines.append(f"{'FORMAT' if row['format'] else 'KEEP':6}  {row['device']}  →  {row['mount']}  ({row['filesystem']})")
    if p['mode'] == 'new':
        lines.append(f"Root: {p['root_gib']} GiB. Boot: 1 GiB. Home: remaining space.")
    lines += ['', 'Bootloader: GRUB / ' + receipt['firmware'].upper() + ' on ' + p['disk']]
    if receipt['firmware'] == 'uefi':
        lines.append('EFI/alpine and the EFI fallback loader will be written; existing filesystems are preserved when marked KEEP.')
    lines += [f"Account: {p['username']} (administrator; password required)",
              f"Computer: {p['hostname']}    Timezone: {p['timezone']}",
              'Desktop and keyboard defaults: this live image; login requires a password.', '',
              'Core: native Alpine, X11/Enlightenment, networking, audio, hardware and recovery tools.',
              'Optional APKs: ' + (', '.join(p['apk']) or 'none'),
              'Flatpak apps: ' + (', '.join(p['flatpak']) or 'none'), '',
              'No Windows data is migrated automatically. Back up before installing.',
              'Network access to the configured signed APK repositories is required.']
    return '\n'.join(lines)


def prepare(receipt, mountroot):
    """Only call after confirming the same receipt and preparing the overlay."""
    p, rows = receipt['plan'], receipt['partitions']
    if p['mode'] == 'new':
        first = 'size=512MiB, type=U' if receipt['firmware'] == 'uefi' else f'size=2MiB, type={BIOS_GUID}'
        layout = f"label: gpt\n{first}\nsize=1GiB, type=L\nsize={p['root_gib']}GiB, type=L\ntype=L\n"
        print('Creating the reviewed GPT layout...', flush=True)
        run('sfdisk', '--wipe', 'always', p['disk'], input=layout, text=True)
        run('partprobe', p['disk'])
        for _ in range(50):
            if all(Path(r['device']).exists() for r in rows):
                break
            time.sleep(.1)
        else:
            raise ValueError('Kernel did not expose the new partitions.')
    for row in rows:
        if row['format']:
            print('Formatting ' + row['device'] + ' for ' + row['mount'], flush=True)
            if row['filesystem'] == 'vfat':
                run('mkfs.vfat', '-F', '32', row['device'])
            else:
                run('mkfs.ext4', '-F', row['device'])
    mounted = []
    try:
        for row in sorted(rows, key=lambda r: len(r['mount'])):
            if not row['mount'].startswith('/'):
                continue
            path = mountroot / row['mount'].lstrip('/')
            path.mkdir(parents=True, exist_ok=True)
            run('mount', row['device'], str(path))
            mounted.append(path)
    except BaseException:
        unmount(mounted)
        raise
    return mounted


def unmount(mounted):
    failed = []
    for path in reversed(mounted):
        if subprocess.run(['umount', str(path)]).returncode:
            failed.append(str(path))
    if failed:
        raise RuntimeError('Could not unmount: ' + ', '.join(failed) + '. Do not remove the target yet.')
