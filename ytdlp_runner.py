#!/usr/bin/env python3
"""
AvocadoDL - Dynamic yt-dlp Launcher & Social Media Resolver
Provides high-resiliency video extraction for Free Download Manager.

Features:
1. TikTok specialized no-watermark resolver (HD, SD, Audio) via pure-Python.
2. Dynamic yt-dlp loader prioritizing updated user packages > system > bundled.
3. Resilient YouTube multi-client fallback (android_vr, web_safari, android, web).
4. Automatic JavaScript engine path detection (Deno / Node on macOS & Windows).
"""

import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Add current directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from config_loader import PACKAGES_DIR, SETTINGS_DIR
except ImportError:
    SETTINGS_DIR = Path.home() / ".avocadodl"
    PACKAGES_DIR = SETTINGS_DIR / "packages"

BUNDLED_DIR = SCRIPT_DIR / "yt-dlp"

# ─── 1. Setup Python Module Search Path ─────────────────────────────────────
# Priority:
# 1. User config packages dir (updated via ytdlp_helper.py)
# 2. Bundled fallback dir inside the add-on
if (PACKAGES_DIR / "yt_dlp").exists():
    sys.path.insert(0, str(PACKAGES_DIR))
elif (BUNDLED_DIR / "yt_dlp").exists():
    sys.path.insert(0, str(BUNDLED_DIR))

# ─── 2. Setup Environment Paths (macOS GUI App PATH Fix) ────────────────────
def configure_environment():
    # macOS GUI apps (like FDM) often lack Homebrew and user bin directories in PATH
    extra_paths = []
    if sys.platform == "darwin":
        extra_paths = [
            "/opt/homebrew/bin",
            "/usr/local/bin",
            str(Path.home() / ".deno/bin"),
            str(Path.home() / ".nvm/versions/node"),
            str(Path.home() / ".local/bin"),
        ]
    elif sys.platform == "win32":
        extra_paths = [
            str(Path.home() / ".deno" / "bin"),
            str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "deno"),
        ]

    current_path = os.environ.get("PATH", "")
    for p in extra_paths:
        if os.path.exists(p) and p not in current_path:
            current_path = p + os.pathsep + current_path
    os.environ["PATH"] = current_path

configure_environment()

# ─── 3. TikTok Direct No-Watermark Resolver ─────────────────────────────────
def is_tiktok_url(url):
    return bool(re.search(r"https?://(?:[a-zA-Z0-9_-]+\.)?tiktok\.com/", url, re.IGNORECASE))

def resolve_tiktok(url):
    """
    Directly extracts no-watermark HD and SD video streams from TikTok.
    Bypasses anti-scraping blocks that cause yt-dlp to fail on TikTok.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.tiktok.com/"
    }

    try:
        post_data = f"url={urllib.parse.quote(url)}&hd=1".encode("utf-8")
        req = urllib.request.Request(
            "https://www.tikwm.com/api/",
            data=post_data,
            headers={
                "User-Agent": headers["User-Agent"],
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            }
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("code") == 0 and data.get("data"):
            d = data["data"]
            formats = []

            # 1. HD No Watermark format
            if d.get("hdplay"):
                formats.append({
                    "format_id": "hd",
                    "format": "hd - 1080p (No Watermark)",
                    "format_note": "HD (No Watermark)",
                    "url": d["hdplay"],
                    "ext": "mp4",
                    "vcodec": "h264",
                    "acodec": "aac",
                    "filesize": d.get("hd_size") or None,
                    "http_headers": headers,
                    "protocol": "https"
                })

            # 2. SD No Watermark format
            if d.get("play"):
                formats.append({
                    "format_id": "sd",
                    "format": "sd - Original (No Watermark)",
                    "format_note": "SD (No Watermark)",
                    "url": d["play"],
                    "ext": "mp4",
                    "vcodec": "h264",
                    "acodec": "aac",
                    "filesize": d.get("size") or None,
                    "http_headers": headers,
                    "protocol": "https"
                })

            # 3. Audio Only format
            if d.get("music"):
                formats.append({
                    "format_id": "audio",
                    "format": "audio - MP3",
                    "format_note": "Audio Only",
                    "url": d["music"],
                    "ext": "mp3",
                    "vcodec": "none",
                    "acodec": "mp3",
                    "http_headers": headers,
                    "protocol": "https"
                })

            if formats:
                video_id = str(d.get("id") or "tiktok_video")
                author_info = d.get("author") or {}
                author_name = author_info.get("nickname") or author_info.get("unique_id") or "TikTok Creator"
                title = d.get("title") or f"TikTok by {author_name}"

                result = {
                    "id": video_id,
                    "title": title,
                    "description": d.get("title", ""),
                    "thumbnail": d.get("cover") or d.get("origin_cover"),
                    "duration": d.get("duration"),
                    "uploader": author_name,
                    "uploader_id": author_info.get("unique_id"),
                    "formats": formats,
                    "extractor": "TikTok",
                    "extractor_key": "TikTok",
                    "webpage_url": url,
                    "original_url": url
                }
                return result
    except Exception as e:
        # Fall back to standard yt-dlp if resolver fails
        pass

    return None

# ─── 4. Argument Enhancements ───────────────────────────────────────────────
def enhance_arguments(args):
    """
    Injects resilient player clients for YouTube to prevent 403 Forbidden errors
    without requiring constant yt-dlp updates.
    """
    target_url = None
    for arg in args:
        if arg.startswith("http://") or arg.startswith("https://"):
            target_url = arg
            break

    enhanced = list(args)

    # Check if target is YouTube
    is_youtube = target_url and bool(re.search(r"https?://(?:[a-zA-Z0-9_-]+\.)?(?:youtube\.com|youtu\.be)/", target_url, re.IGNORECASE))

    if is_youtube:
        has_extractor_args = any(a == "--extractor-args" for a in enhanced)
        has_youtube_client = any("youtube:player_client" in a for a in enhanced)

        if not has_youtube_client:
                # Use default clients (android_vr, web_safari) plus android for maximum resilience and format options
                enhanced.insert(0, "--extractor-args")
                enhanced.insert(1, "youtube:player_client=default,android")

    return target_url, enhanced

# ─── 5. Main Execution Entrypoint ───────────────────────────────────────────
def main():
    raw_args = sys.argv[1:]
    target_url, final_args = enhance_arguments(raw_args)

    # 1. Specialized TikTok Check
    if target_url and is_tiktok_url(target_url):
        tiktok_res = resolve_tiktok(target_url)
        if tiktok_res:
            # Emit standard JSON expected by FDM
            sys.stdout.buffer.write(json.dumps(tiktok_res, ensure_ascii=False).encode("utf-8"))
            sys.stdout.buffer.write(b"\n")
            sys.stdout.buffer.flush()
            return 0

    # 2. Delegate to yt_dlp
    try:
        import yt_dlp
    except ImportError:
        sys.stderr.write("ERROR: yt-dlp module could not be loaded.\n")
        return 1

    sys.argv = [sys.argv[0]] + final_args
    try:
        return yt_dlp.main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 0

if __name__ == "__main__":
    sys.exit(main() or 0)
