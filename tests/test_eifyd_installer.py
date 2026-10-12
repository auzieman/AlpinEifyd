import importlib.util
import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'aports/eifyd-installer'))
spec = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] /
    'aports/eifyd-installer/eifyd-install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTest(unittest.TestCase):
    def test_flatpak_operations_select_target_without_changing_host_environment(self):
        with patch.object(installer, 'run') as command, patch.dict(os.environ, {}, clear=False):
            before = os.environ.get('FLATPAK_SYSTEM_DIR')
            installer.target_flatpak(Path('/mnt/target/var/lib/flatpak'), 'list', '--system')
            self.assertEqual(command.call_args.args, ('flatpak', 'list', '--system'))
            self.assertEqual(command.call_args.kwargs['env']['FLATPAK_SYSTEM_DIR'],
                             '/mnt/target/var/lib/flatpak')
            self.assertEqual(os.environ.get('FLATPAK_SYSTEM_DIR'), before)

    def test_saved_plan_revalidates_and_rejects_unknown_operations(self):
        plan = dict(disk='/dev/sdb', hostname='desktop', username='tester', timezone='UTC')
        normalized = installer.storage.normalize(plan)
        self.assertEqual(normalized['username'], 'tester')
        plan['preserve_home'] = True
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            installer.storage.normalize(plan)

    def test_console_cancel_never_installs(self):
        with patch.object(installer, 'disks', return_value=[]), \
             patch('builtins.input', return_value=''), \
             patch.object(installer, 'install') as execute:
            installer.tui()
            execute.assert_not_called()

    def test_changed_review_never_reaches_password_hash_or_disk_commands(self):
        with patch.object(installer.os, 'geteuid', return_value=0), \
             patch.object(installer.storage, 'inspect', return_value=({}, 'new-token')), \
             patch.object(installer, 'run') as commands:
            with self.assertRaisesRegex(ValueError, 'changed'):
                installer.install({}, 'old-token', 'test-password')
            commands.assert_not_called()

    def test_failed_unmount_does_not_trigger_recursive_target_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory) / 'work'
            work.mkdir()
            target_file = work / 'target-file'
            target_file.write_text('must survive cleanup')
            with patch.object(installer.tempfile, 'mkdtemp', return_value=str(work)), \
                 patch.object(Path, 'read_text', return_value=f'1 2 3 / {work}/target rw - ext4 /dev/sdb3 rw\n'):
                with installer.workspace():
                    pass
            self.assertEqual(target_file.read_text(), 'must survive cleanup')

    def test_mounted_disk_and_swap_are_rejected(self):
        for mounts in (['/'], ['[SWAP]']):
            with patch.object(installer.storage, 'disks', return_value=[dict(
                path='/dev/sda', type='disk', size=100 * 1024**3,
                children=[dict(type='part', mountpoints=mounts)])]):
                with self.assertRaisesRegex(ValueError, 'in use'):
                    installer.storage.inspect(dict(disk='/dev/sda', username='tester'))

    def test_confirmation_binds_disk_identity_and_software(self):
        disk = dict(path='/dev/sdb', type='disk', size=100 * 1024**3, serial='first')
        with patch.object(installer.storage, 'disks', return_value=[disk]), \
             patch.object(installer.storage, 'firmware_mode', return_value='bios'), \
             patch.object(installer.storage, 'minimum_root', return_value=24):
            plan = dict(disk='/dev/sdb', username='tester')
            receipt, first = installer.storage.inspect(plan)
            self.assertEqual([r['mount'] for r in receipt['partitions']][-2:], ['/', '/home'])
            disk['serial'] = 'replacement'
            self.assertNotEqual(first, installer.storage.inspect(plan)[1])
            disk['serial'] = 'first'
            self.assertNotEqual(first, installer.storage.inspect(plan | {'apk': []})[1])

    def test_preserved_home_cannot_be_root_or_non_ext4(self):
        disk = dict(path='/dev/sdb', type='disk', pttype='dos', size=100 * 1024**3,
                    children=[dict(path='/dev/sdb1', type='part', size=50*1024**3, fstype='ext4'),
                              dict(path='/dev/sdb2', type='part', size=49*1024**3, fstype='ntfs')])
        with patch.object(installer.storage, 'disks', return_value=[disk]), \
             patch.object(installer.storage, 'firmware_mode', return_value='bios'), \
             patch.object(installer.storage, 'minimum_root', return_value=24):
            plan = dict(disk='/dev/sdb', username='tester', mode='existing',
                        root='/dev/sdb1', home='/dev/sdb1')
            with self.assertRaisesRegex(ValueError, 'distinct'):
                installer.storage.inspect(plan)
            plan['home'] = '/dev/sdb2'
            with self.assertRaisesRegex(ValueError, 'ext4'):
                installer.storage.inspect(plan)

    def test_package_choices_keep_base_and_filter_versioned_optional_names(self):
        world = ['alpine-base', 'sudo', 'firefox=1.2', 'git@stable', 'podman']
        self.assertEqual(installer.selected_world({'apk': ['firefox']}, world),
                         ['alpine-base', 'sudo', 'firefox=1.2'])

    def test_live_account_and_autologin_do_not_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'overlay'
            source = Path(directory) / 'source'
            etc = root / 'etc'
            for folder in ('skel', 'sudoers.d', 'doas.d', 'lightdm/lightdm.conf.d', 'ssh'):
                (etc / folder).mkdir(parents=True, exist_ok=True)
            (source / 'usr/share/zoneinfo').mkdir(parents=True)
            (source / 'usr/share/zoneinfo/UTC').write_text('zone-data')
            (source / 'usr/local/bin').mkdir(parents=True)
            (source / 'usr/local/bin/helper').write_text('helper')
            (etc / 'passwd').write_text('root:x:0:0:root:/root:/bin/ash\nalpine:x:1000:1000:live:/home/alpine:/bin/ash\n')
            (etc / 'shadow').write_text('root::20000:0:99999:7:::\nalpine::20000:0:99999:7:::\n')
            (etc / 'group').write_text('alpine:x:1000:\nwheel:x:10:alpine\naudio:x:18:alpine\n')
            (etc / 'sudoers.d/alpine-live').write_text('alpine ALL=(ALL) NOPASSWD: ALL')
            (etc / 'doas.d/live.conf').write_text('permit nopass alpine')
            (etc / 'machine-id').write_text('live-machine')
            (etc / 'ssh/ssh_host_test_key').write_text('live-key')
            config = etc / 'lightdm/lightdm.conf.d/50-alpine.conf'
            config.write_text('[Seat:*]\nuser-session=enlightenment\nautologin-user=alpine\nautologin-user-timeout=0\n')
            (etc / 'skel/.xsession').write_text('exec enlightenment_start\n')
            # A copied live symlink must not cause writes outside the overlay.
            (etc / 'localtime').symlink_to(source / 'usr/share/zoneinfo/UTC')
            with patch.object(installer.os, 'chown'):
                installer.configure_overlay(root, dict(username='tester', hostname='desktop', timezone='UTC'), '$6$hash', source)
            self.assertNotIn('alpine:', (etc / 'passwd').read_text())
            self.assertIn('tester:x:1000:1000', (etc / 'passwd').read_text())
            self.assertIn('root:!:', (etc / 'shadow').read_text())
            self.assertIn('tester:$6$hash:', (etc / 'shadow').read_text())
            self.assertIn('wheel:x:10:tester', (etc / 'group').read_text())
            self.assertNotIn('autologin', config.read_text())
            self.assertFalse((etc / 'sudoers.d/alpine-live').exists())
            self.assertFalse((etc / 'ssh/ssh_host_test_key').exists())
            self.assertFalse((etc / 'machine-id').exists())
            self.assertTrue((root / 'home/tester/.xsession').is_file())
            self.assertEqual((etc / 'shadow').stat().st_mode & 0o777, 0o600)
            self.assertTrue((root / 'usr/local/bin/helper').is_file())


if __name__ == '__main__':
    unittest.main()
