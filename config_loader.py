import json, os, sys
from pathlib import Path

SETTINGS_DIR = Path(os.environ.get("APPDATA", Path.home())) / "avocadodl"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

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
            with open(SETTINGS_FILE) as f:
                user = json.load(f)
            merged = dict(DEFAULT_SETTINGS)
            merged.update(user)
            return merged
    except Exception:
        pass
    return dict(DEFAULT_SETTINGS)

def save(settings):
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

if __name__ == "__main__":
    settings = load()
    if not SETTINGS_FILE.exists():
        save(settings)
    print(json.dumps(settings))
