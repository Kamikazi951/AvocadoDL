"""Exercise the built archive using real yt-dlp against a local fixture server."""
import functools
import http.server
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        version = json.loads((ROOT / 'manifest.json').read_text())['version']
        archive = ROOT / ('avocadodl-' + version + '.fda')
        if not archive.exists():
            raise unittest.SkipTest('Build the .fda first with python build.py')
        cls.temporary = tempfile.TemporaryDirectory(prefix='avocadodl-package-test-')
        cls.folder = Path(cls.temporary.name)
        cls.addon = cls.folder / 'addon'
        with zipfile.ZipFile(archive) as package:
            package.extractall(cls.addon)
        cls.web = cls.folder / 'web'
        cls.web.mkdir()
        (cls.web / 'index.html').write_text('<title>Fixture video</title><video controls src="sample.mp4"></video>')
        (cls.web / 'sample.mp4').write_bytes(b'fixture media bytes')
        (cls.web / 'master.m3u8').write_text('#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360,CODECS="avc1.42e01e,mp4a.40.2"\nvariant.m3u8\n')
        (cls.web / 'variant.m3u8').write_text('#EXTM3U\n#EXT-X-TARGETDURATION:10\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:10,\nsegment.ts\n#EXT-X-ENDLIST\n')
        (cls.web / 'video.mpd').write_text('<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static" mediaPresentationDuration="PT10S"><Period><AdaptationSet mimeType="video/mp4"><Representation id="v" bandwidth="800000" width="640" height="360" codecs="avc1.42e01e"><BaseURL>sample.mp4</BaseURL></Representation></AdaptationSet></Period></MPD>')
        cls.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(cls.web)))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temporary.cleanup()

    def extract(self, target):
        # Isolated config/cache: never access the user's cookies or settings.
        env = {**os.environ, 'APPDATA': str(self.folder / 'config'), 'XDG_CONFIG_HOME': str(self.folder / 'config')}
        result = subprocess.run([sys.executable, str(self.addon / 'ytdlp_runner.py'),
            '--ignore-config', '--no-plugin-dirs', '--no-cache-dir', '-J', '--skip-download',
            '--socket-timeout', '5', '--no-playlist', '--', self.base + target],
            capture_output=True, text=True, encoding='utf-8', env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_bundled_ejs_is_importable_without_global_packages(self):
        result = subprocess.run([sys.executable, '-I', '-c',
            'import sys, json; sys.path.insert(0, sys.argv[1]); import yt_dlp_ejs; from importlib.metadata import version, requires; print(json.dumps({"version": version("yt-dlp-ejs"), "requirements": requires("yt-dlp")}))',
            str(self.addon / 'yt-dlp')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        bundled = json.loads(result.stdout)
        requirement = 'yt-dlp-ejs==' + bundled['version']
        self.assertTrue(any(item.split(';')[0].replace(' ', '') == requirement
                            for item in bundled['requirements']),
                        'Bundled EJS must match the bundled yt-dlp requirement')

    def test_html_player_is_resolved_to_media(self):
        result = self.extract('/index.html?fdmguid=6d36f5b5519148d69647a983ebd677fc')
        self.assertIn('sample.mp4', json.dumps(result))
        self.assertNotIn('fdmguid', result.get('original_url', ''))

    def test_hls_master_returns_formats(self):
        result = self.extract('/master.m3u8')
        self.assertTrue(result['formats'])
        self.assertEqual(result['formats'][0]['height'], 360)

    def test_dash_manifest_returns_formats(self):
        result = self.extract('/video.mpd')
        self.assertTrue(result['formats'])
        self.assertEqual(result['formats'][0]['height'], 360)

    def test_direct_file(self):
        result = self.extract('/sample.mp4')
        self.assertEqual(result['url'], self.base + '/sample.mp4')


if __name__ == '__main__':
    unittest.main()
