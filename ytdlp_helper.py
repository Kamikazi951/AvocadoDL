import io
import json
import os
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from config_loader import PACKAGES_DIR, SETTINGS_DIR
except ImportError:
    SETTINGS_DIR = Path.home() / ".avocadodl"
    PACKAGES_DIR = SETTINGS_DIR / "packages"

ADDON_DIR = Path(__file__).resolve().parent
BUNDLED_DIR = ADDON_DIR / "yt-dlp" / "yt_dlp"
CACHED_DIR = PACKAGES_DIR / "yt_dlp"

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
USER_AGENT = "Mozilla/5.0 (compatible; AvocadoDL/1.1; +https://github.com/Kamikazi951/avocadodl)"

def parse_version_tuple(v):
    try:
        return tuple(int(x) for x in re.findall(r"\d+", str(v)))
    except Exception:
        return (0,)

def read_version_from_dir(directory):
    try:
        ver_file = directory / "version.py"
        if ver_file.exists():
            src = ver_file.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)', src)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def get_cached_version():
    return read_version_from_dir(CACHED_DIR)

def get_bundled_version():
    return read_version_from_dir(BUNDLED_DIR)

def get_system_version():
    try:
        import yt_dlp.version
        return yt_dlp.version.__version__
    except Exception:
        pass
    return None

def get_active_version():
    cached = get_cached_version()
    if cached:
        return cached
    bundled = get_bundled_version()
    if bundled:
        return bundled
    return get_system_version()

def fetch_pypi_info():
    try:
        req = urllib.request.Request(PYPI_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            latest_version = data.get("info", {}).get("version")
            wheel_url = None
            for file_info in data.get("urls", []):
                u = file_info.get("url", "")
                if u.endswith("-none-any.whl"):
                    wheel_url = u
                    break
            return latest_version, wheel_url
    except Exception:
        return None, None

def update_from_wheel(wheel_url):
    try:
        PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(wheel_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=45) as resp:
            content = resp.read()

        tmp_extract_dir = PACKAGES_DIR / "_yt_dlp_tmp"
        if tmp_extract_dir.exists():
            shutil.rmtree(tmp_extract_dir, ignore_errors=True)
        tmp_extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            for member in zf.namelist():
                if member.startswith("yt_dlp/"):
                    zf.extract(member, tmp_extract_dir)

        extracted_pkg = tmp_extract_dir / "yt_dlp"
        if not extracted_pkg.exists() or not (extracted_pkg / "__main__.py").exists():
            shutil.rmtree(tmp_extract_dir, ignore_errors=True)
            return False

        if CACHED_DIR.exists():
            try:
                shutil.rmtree(CACHED_DIR, ignore_errors=True)
            except Exception:
                old_dir = PACKAGES_DIR / "_yt_dlp_old"
                if old_dir.exists():
                    shutil.rmtree(old_dir, ignore_errors=True)
                shutil.move(str(CACHED_DIR), str(old_dir))

        shutil.move(str(extracted_pkg), str(CACHED_DIR))
        shutil.rmtree(tmp_extract_dir, ignore_errors=True)
        return True
    except Exception:
        return False

def check_and_update():
    active_ver = get_active_version()
    latest_ver, wheel_url = fetch_pypi_info()
    updated = False

    if latest_ver and wheel_url:
        if not active_ver or parse_version_tuple(latest_ver) > parse_version_tuple(active_ver):
            if update_from_wheel(wheel_url):
                updated = True
                active_ver = get_cached_version() or latest_ver

    return {
        "active_version": active_ver,
        "latest_pypi_version": latest_ver,
        "updated": updated
    }

if __name__ == "__main__":
    result = check_and_update()
    print(json.dumps(result))
