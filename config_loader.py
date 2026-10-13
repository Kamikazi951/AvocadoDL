import json, os, sys
from pathlib import Path

def get_settings_dir():
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "avocadodl"
        return Path.home() / "AppData" / "Roaming" / "avocadodl"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "avocadodl"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "avocadodl"
        return Path.home() / ".config" / "avocadodl"

SETTINGS_DIR = get_settings_dir()
SETTINGS_FILE = SETTINGS_DIR / "settings.json"
PACKAGES_DIR = SETTINGS_DIR / "packages"

DEFAULT_SETTINGS = {
    "format": "bestvideo*+bestaudio/best",
    "output_template": "%(title)s.%(ext)s",
    "extra_ytdlp_args": [],
    "auto_update_ytdlp": True,
    "cookies_browser": "",
    "embed_thumbnail": False,
    "extract_audio": False,
    "audio_format": "mp3",
    "audio_quality": "192",
    "write_subs": False,
    "sub_langs": "en",
    "download_archive": "",
    "limit_rate": "",
    "proxy": ""
}

def load():
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, encoding="utf-8-sig") as f:
                user = json.load(f)
            if not isinstance(user, dict):
                return dict(DEFAULT_SETTINGS)
            merged = dict(DEFAULT_SETTINGS)
            for key, default in DEFAULT_SETTINGS.items():
                value = user.get(key, default)
                if isinstance(value, type(default)):
                    merged[key] = value
            if not all(isinstance(arg, str) for arg in merged['extra_ytdlp_args']):
                merged['extra_ytdlp_args'] = []
            return merged
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)

def save(settings):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

if __name__ == "__main__":
    settings = load()
    if not SETTINGS_FILE.exists():
        save(settings)
    print(json.dumps(settings))
