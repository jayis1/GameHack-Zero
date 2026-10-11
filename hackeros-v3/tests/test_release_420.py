import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


class ReleaseTests(unittest.TestCase):
    def test_identifiers_are_consistent(self):
        self.assertIn('VERSION = "4.2.0"', (ROOT / 'staging/opt/hackeros/launcher.py').read_text())
        self.assertIn('VERSION_ID="4.2.0"', (ROOT / 'staging/os-release').read_text())
        self.assertIn('VERSION="4.2.0"', (ROOT / 'staging/etc/hackeros/release').read_text())

    def test_installer_rejects_sensitive_and_boot_configuration_paths(self):
        installer = module('release_installer', 'install-release-4.2.0.py')
        for path in ('../etc/passwd', '/etc/passwd', 'etc/passwd', 'etc/shadow',
                     'home/hacker/.ssh/id_ed25519', 'etc/NetworkManager/system-connections/pi',
                     'boot/u-boot/boot.ini', 'boot/dtb/rockchip/rk3326-gameconsole-r36s.dtb'):
            self.assertFalse(installer.safe_target(path), path)

    def test_manifest_is_bounded_to_release_sources(self):
        builder = module('release_builder', 'build-release-4.2.0.py')
        installer = module('release_paths', 'install-release-4.2.0.py')
        manifest = builder.payload()
        targets = [r['target'] for r in manifest['files']]
        self.assertEqual(len(targets), len(set(targets)))
        self.assertTrue(all(installer.safe_target(p) for p in targets))
        self.assertIn('opt/hackeros/ir_library.py', targets)
        self.assertIn('opt/hackeros/nimbus_fieldkit.py', targets)
        self.assertIn('usr/local/lib/gamehack-zero/sd2_state.py', targets)
        self.assertNotIn('usr/local/bin/opencode', targets)
        self.assertFalse(any('__pycache__' in p or '.pre-' in p for p in targets))

    def test_optional_sandisk_documented(self):
        text = (ROOT / 'staging/opt/hackeros/nimbus_fieldkit.py').read_text()
        self.assertIn("'sandisk_required': False", text)
        self.assertIn('OPTIONAL FIELD NODE', text)
