"""Verified, versioned yt-dlp + EJS updates. Never overwrite a running package."""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from config_loader import PACKAGES_DIR, SETTINGS_DIR

BUNDLED_ROOT = Path(__file__).resolve().parent / 'yt-dlp'
USER_AGENT = 'AvocadoDL/1.1'


def parse_version_tuple(value):
    return tuple(int(part) for part in re.findall(r'\d+', str(value))) or (0,)


def read_version_from_dir(directory):
    try:
        text = (directory / 'version.py').read_text(encoding='utf-8')
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)', text)
        return match.group(1) if match else None
    except OSError:
        return None


def active_package_root():
    candidates = [BUNDLED_ROOT, PACKAGES_DIR]
    try:
        name = json.loads((PACKAGES_DIR / 'active.json').read_text(encoding='utf-8'))['directory']
        if isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            candidates.insert(0, PACKAGES_DIR / 'releases' / name)
    except (OSError, ValueError, KeyError, TypeError):
        pass
    candidates = [p for p in candidates if (p / 'yt_dlp' / '__main__.py').is_file()]
    # On equal versions prefer a complete package with its companion solver.
    return max(candidates, key=lambda p: (parse_version_tuple(read_version_from_dir(p / 'yt_dlp')),
                                        (p / 'yt_dlp_ejs').is_dir()), default=None)


def get_active_version():
    root = active_package_root()
    return read_version_from_dir(root / 'yt_dlp') if root else None


def fetch_json(url):
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.load(response)


def extract_wheel(info, destination, package):
    wheel = next(item for item in info['urls'] if item['filename'].endswith('-none-any.whl'))
    if not wheel['url'].startswith('https://files.pythonhosted.org/'):
        raise ValueError('Unexpected package download host')
    request = urllib.request.Request(wheel['url'], headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(40 * 1024 * 1024 + 1)
    if len(data) > 40 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != wheel['digests']['sha256']:
        raise ValueError('Package integrity check failed')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in member.filename or not path.parts:
                raise ValueError('Unsafe package path')
            if path.parts[0] != package and not (path.parts[0].startswith(package + '-') and path.parts[0].endswith('.dist-info')):
                continue
            archive.extract(member, destination)


def solver_version(info):
    for dependency in info['info'].get('requires_dist') or []:
        match = re.match(r'yt-dlp-ejs\s*==\s*([\w.]+)', dependency)
        if match:
            return match.group(1)
    raise ValueError('Unknown EJS dependency; keeping the working package')


def check_and_update(force=False):
    result = {'active_version': get_active_version(), 'updated': False}
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = SETTINGS_DIR / 'last-update-check.json'
    try:
        if not force and time.time() - stamp.stat().st_mtime < 3600:
            return result
    except OSError:
        pass
    lock = SETTINGS_DIR / 'update.lock'
    try:
        # An interrupted updater cannot hold the lock forever.
        if lock.exists() and time.time() - lock.stat().st_mtime > 600:
            lock.unlink()
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return {**result, 'status': 'another_update_running'}
    os.close(descriptor)
    staging = None
    try:
        info = fetch_json('https://pypi.org/pypi/yt-dlp/json')
        latest = info['info']['version']
        result['latest_pypi_version'] = latest
        root = active_package_root()
        if parse_version_tuple(latest) < parse_version_tuple(result['active_version']):
            return result
        if parse_version_tuple(latest) == parse_version_tuple(result['active_version']) and root and (root / 'yt_dlp_ejs').is_dir():
            return result
        releases = PACKAGES_DIR / 'releases'
        releases.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='staging-', dir=releases))
        extract_wheel(info, staging, 'yt_dlp')
        ejs = fetch_json('https://pypi.org/pypi/yt-dlp-ejs/' + solver_version(info) + '/json')
        extract_wheel(ejs, staging, 'yt_dlp_ejs')
        # Validate with this exact interpreter before changing the active pointer.
        subprocess.run([sys.executable, '-I', '-c',
            'import sys; sys.path.insert(0, sys.argv[1]); import yt_dlp, yt_dlp_ejs', str(staging)],
            check=True, capture_output=True, timeout=20)
        name = latest + '-' + uuid.uuid4().hex[:8]
        staging.rename(releases / name)
        staging = None
        pointer = PACKAGES_DIR / ('active-' + uuid.uuid4().hex + '.tmp')
        pointer.write_text(json.dumps({'directory': name}), encoding='utf-8')
        os.replace(pointer, PACKAGES_DIR / 'active.json')
        result.update(active_version=latest, updated=True)
    except Exception as error:
        # Offline or incompatible updates must leave extraction usable.
        result['status'] = 'update_failed_using_existing_package'
        result['error_type'] = type(error).__name__
    finally:
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
        try:
            stamp.write_text(json.dumps(result), encoding='utf-8')
        finally:
            lock.unlink(missing_ok=True)
    return result


if __name__ == '__main__':
    print(json.dumps(check_and_update(force='--force' in sys.argv)))
