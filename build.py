"""Build a portable .fda with verified yt-dlp and its matching EJS dependency."""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from ytdlp_helper import extract_wheel, fetch_json, solver_version

ROOT = Path(__file__).resolve().parent
FILES = ['manifest.json', 'icon.svg', 'tools.js', 'msabstractparser.js', 'msparser.js',
         'msbatchparser.js', 'config_loader.py', 'ytdlp_helper.py', 'ytdlp_runner.py',
         'settings.template.json', 'LICENSE']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version')
    parser.add_argument('--output')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    if args.version:
        manifest['version'] = args.version
    output = ROOT / (args.output or ('avocadodl-' + manifest['version'] + '.fda'))
    with tempfile.TemporaryDirectory(prefix='avocadodl-build-') as temporary:
        dependencies = Path(temporary)
        if args.offline:
            dependencies = ROOT / 'yt-dlp'
        else:
            info = fetch_json('https://pypi.org/pypi/yt-dlp/json')
            extract_wheel(info, dependencies, 'yt_dlp')
            ejs = fetch_json('https://pypi.org/pypi/yt-dlp-ejs/' + solver_version(info) + '/json')
            extract_wheel(ejs, dependencies, 'yt_dlp_ejs')
        subprocess.run([sys.executable, '-I', '-c',
            'import sys; sys.path.insert(0, sys.argv[1]); import yt_dlp, yt_dlp_ejs; from yt_dlp.version import __version__; print("Bundling yt-dlp", __version__)',
            str(dependencies)], check=True)
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in FILES:
                if name == 'manifest.json':
                    archive.writestr(name, json.dumps(manifest, indent=2))
                else:
                    archive.write(ROOT / name, name)
            for path in sorted(dependencies.rglob('*')):
                if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                    archive.write(path, 'yt-dlp/' + path.relative_to(dependencies).as_posix())
    print('Built', output, '(' + str(output.stat().st_size) + ' bytes)')


if __name__ == '__main__':
    main()
