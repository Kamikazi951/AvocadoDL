import json, os, subprocess, sys
from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent
BUNDLED_MAIN = ADDON_DIR / "yt-dlp" / "yt_dlp" / "__main__.py"

def get_system_version():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None

def get_bundled_version():
    try:
        ver_file = ADDON_DIR / "yt-dlp" / "yt_dlp" / "version.py"
        if ver_file.exists():
            src = ver_file.read_text()
            import re
            m = re.search(r'__version__\s*=\s*["\']([^"\']+)', src)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None

def update_system():
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
            capture_output=True, text=True, timeout=120
        )
        return True
    except Exception:
        return False

def compare_versions(a, b):
    try:
        from pkg_resources import parse_version
        return (parse_version(a) >= parse_version(b))
    except Exception:
        return False

if __name__ == "__main__":
    sys_ver = get_system_version()
    bdl_ver = get_bundled_version()
    updated = False

    if sys_ver and bdl_ver and not compare_versions(sys_ver, bdl_ver):
        updated = update_system()
        sys_ver = get_system_version()

    print(json.dumps({
        "system_version": sys_ver,
        "bundled_version": bdl_ver,
        "updated": updated
    }))
