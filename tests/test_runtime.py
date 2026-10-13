import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config_loader
import ytdlp_helper as helper
import ytdlp_runner as runner


class RuntimeTests(unittest.TestCase):
    def test_target_is_last_not_proxy_and_signed_query_survives(self):
        args = ['--proxy', 'http://proxy.invalid', '--referer', 'https://ref.invalid', '--',
                'https://youtu.be/abc?sig=a%20b%2Fc+z&fdmguid=123#t=5']
        target, enhanced = runner.enhance_arguments(args)
        self.assertEqual(target, 'https://youtu.be/abc?sig=a%20b%2Fc+z#t=5')
        self.assertNotIn('--extractor-args', enhanced)
        self.assertIn('http://proxy.invalid', enhanced)

    def test_cookie_fallback_preserves_other_options(self):
        self.assertEqual(runner.without_browser_cookies(['--cookies-from-browser', 'chrome', '--cookies', 'export.txt', '--', 'https://example.org']),
                         ['--cookies', 'export.txt', '--', 'https://example.org'])
        self.assertEqual(runner.without_browser_cookies(['--cookies-from-browser=chrome', 'url']), ['url'])

    def test_cookie_database_error_retries_public_extraction(self):
        with patch.object(runner, 'active_package_root', return_value=None), patch.dict(sys.modules, {'yt_dlp': object()}), \
             patch.object(runner, 'execute', side_effect=[(1, 'ERROR: Could not copy Chrome cookie database'), (0, '')]) as execute:
            self.assertEqual(runner.main(['--cookies-from-browser', 'chrome', '--', 'https://example.org/video']), 0)
            self.assertNotIn('--cookies-from-browser', execute.call_args.args[1])

    def test_non_cookie_failure_is_not_retried(self):
        with patch.object(runner, 'active_package_root', return_value=None), patch.dict(sys.modules, {'yt_dlp': object()}), \
             patch.object(runner, 'execute', return_value=(1, 'ERROR: DRM protected')) as execute, patch('sys.stderr', io.StringIO()):
            self.assertEqual(runner.main(['--cookies-from-browser', 'chrome', 'https://example.org/video']), 1)
            self.assertEqual(execute.call_count, 1)

    def test_user_runtime_override_is_respected(self):
        for option in ['--js-runtimes=deno:/custom/path', '--no-js-runtimes']:
            _, args = runner.enhance_arguments([option, 'https://example.org'])
            self.assertNotIn('--js-runtimes', args)

    def test_settings_bom_validation_and_unknown_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / 'settings.json'
            file.write_text(json.dumps({'format': ['bad'], 'auto_update_ytdlp': False,
                                       'extra_ytdlp_args': ['--cookies', 42], 'unknown': 'ignored'}), encoding='utf-8-sig')
            with patch.object(config_loader, 'SETTINGS_FILE', file):
                config = config_loader.load()
            self.assertEqual(config['format'], config_loader.DEFAULT_SETTINGS['format'])
            self.assertFalse(config['auto_update_ytdlp'])
            self.assertEqual(config['extra_ytdlp_args'], [])
            self.assertNotIn('unknown', config)

    def package(self, root, version, ejs=False):
        (root / 'yt_dlp').mkdir(parents=True)
        (root / 'yt_dlp' / '__main__.py').touch()
        (root / 'yt_dlp' / 'version.py').write_text('__version__ = ' + repr(version))
        if ejs:
            (root / 'yt_dlp_ejs').mkdir()

    def test_old_cache_cannot_override_newer_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root / 'bundle', '2026.08.19', True)
            self.package(root / 'cache', '2025.01.01')
            with patch.object(helper, 'BUNDLED_ROOT', root / 'bundle'), patch.object(helper, 'PACKAGES_DIR', root / 'cache'):
                self.assertEqual(helper.active_package_root(), root / 'bundle')

    def test_offline_update_keeps_previous_package_and_throttles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(helper, 'SETTINGS_DIR', root), patch.object(helper, 'PACKAGES_DIR', root / 'packages'), \
                 patch.object(helper, 'fetch_json', side_effect=OSError('offline')) as fetch:
                before = helper.get_active_version()
                result = helper.check_and_update()
                self.assertEqual(result['active_version'], before)
                self.assertFalse(result['updated'])
                helper.check_and_update()
                self.assertEqual(fetch.call_count, 1)
                self.assertFalse((root / 'update.lock').exists())

    def test_update_lock_prevents_concurrent_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'update.lock').touch()
            with patch.object(helper, 'SETTINGS_DIR', root), patch.object(helper, 'fetch_json') as fetch:
                self.assertEqual(helper.check_and_update()['status'], 'another_update_running')
                fetch.assert_not_called()

    def test_normalized_version_does_not_reinstall_same_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root / 'bundle', '2026.08.19', True)
            with patch.object(helper, 'SETTINGS_DIR', root), patch.object(helper, 'PACKAGES_DIR', root / 'packages'), \
                 patch.object(helper, 'BUNDLED_ROOT', root / 'bundle'), \
                 patch.object(helper, 'fetch_json', return_value={'info': {'version': '2026.8.19'}}), \
                 patch.object(helper, 'extract_wheel') as extract:
                self.assertFalse(helper.check_and_update()['updated'])
                extract.assert_not_called()

    def test_failed_validation_does_not_replace_active_pointer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            packages = root / 'packages'
            packages.mkdir()
            pointer = packages / 'active.json'
            pointer.write_text('{"directory":"previous"}')
            self.package(packages / 'releases' / 'previous', '2025.01.01', True)
            with patch.object(helper, 'SETTINGS_DIR', root), patch.object(helper, 'PACKAGES_DIR', packages), \
                 patch.object(helper, 'BUNDLED_ROOT', root / 'absent'), \
                 patch.object(helper, 'fetch_json', return_value={'info': {'version':'2026.08.19', 'requires_dist':['yt-dlp-ejs==0.8.0']}}), \
                 patch.object(helper, 'extract_wheel'), patch.object(helper.subprocess, 'run', side_effect=RuntimeError('validation failed')):
                self.assertFalse(helper.check_and_update()['updated'])
                self.assertEqual(json.loads(pointer.read_text())['directory'], 'previous')
                self.assertEqual(helper.get_active_version(), '2025.01.01')

    def wheel(self, name):
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as archive:
            archive.writestr(name, 'fixture')
        data = data.getvalue()
        info = {'urls': [{'filename': 'yt_dlp-1-py3-none-any.whl',
                         'url': 'https://files.pythonhosted.org/fixture.whl',
                         'digests': {'sha256': hashlib.sha256(data).hexdigest()}}]}
        return data, info

    def test_wheel_hash_and_path_traversal_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, tamper in [('yt_dlp/../../escape.py', False), ('yt_dlp/test.py', True)]:
                data, info = self.wheel(name)
                if tamper:
                    info['urls'][0]['digests']['sha256'] = 'wrong'
                with patch.object(helper.urllib.request, 'urlopen', return_value=io.BytesIO(data)):
                    with self.assertRaises(ValueError):
                        helper.extract_wheel(info, Path(directory), 'yt_dlp')

    def test_update_rejects_unexpected_dependency_requirements(self):
        with self.assertRaises(ValueError):
            helper.solver_version({'info': {'requires_dist': ['yt-dlp-ejs>=99']}})


if __name__ == '__main__':
    unittest.main()
