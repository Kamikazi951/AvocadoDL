# AvocadoDL

[![Build](https://github.com/Kamikazi951/avocadodl/actions/workflows/build.yml/badge.svg)](https://github.com/Kamikazi951/avocadodl/actions/workflows/build.yml)

**AvocadoDL** is an add-on for **Free Download Manager 6** that lets you download videos from YouTube, Twitter/X, Instagram, TikTok, Facebook, and hundreds of other sites.

> [!IMPORTANT]
> This FDM Add-on works in pair with the [AvocadoDL Chrome Extension](https://github.com/Kamikazi951/AvocadoDLExtension) which automatically sniffs webpages and sends video download commands to Free Download Manager with one-click!

---

## Install

1. Download the latest `avocadodl.fda` from [Releases](https://github.com/Kamikazi951/avocadodl/releases)
2. Open FDM -- **Tools > Add-ons > Install from file**
3. Select `avocadodl.fda` and restart FDM

**Requirements:**
- **Python 3.8+** ([python.org](https://python.org)) -- the addon runs Python scripts to detect video formats
- **yt-dlp is bundled** inside the `.fda` file -- no separate installation needed
- **Ffmpeg** comes with FDM -- nothing extra to install

---

## Quick Start

1. Copy a video URL
2. FDM detects it automatically and shows download options
3. Choose quality and download

No configuration needed.

---

## Settings

AvocadoDL auto-creates a settings file at `%APPDATA%\avocadodl\settings.json`.

| Setting | Default | Description |
|---|---|---|
| `format` | `bestvideo*+bestaudio/best` | Video format selection |
| `output_template` | `%(title)s.%(ext)s` | File naming pattern |
| `extra_ytdlp_args` | `[]` | Extra yt-dlp arguments |
| `auto_update_ytdlp` | `true` | Auto-update yt-dlp |
| `cookies_browser` | `""` | Browser for cookies (`firefox`, `chrome`, `brave`, `edge`, or empty for auto-detect) |
| `embed_thumbnail` | `false` | Embed thumbnail in file |
| `extract_audio` | `false` | Extract audio only |
| `audio_format` | `mp3` | Audio format (`mp3`, `m4a`, `opus`, `flac`) |
| `audio_quality` | `192` | Audio quality (0-9 or bitrate) |
| `write_subs` | `false` | Download subtitles |
| `sub_langs` | `en` | Subtitle languages (comma-separated) |
| `download_archive` | `""` | Archive file to track downloaded videos |
| `limit_rate` | `""` | Download speed limit (e.g. `5M`, `1M`) |
| `proxy` | `""` | Proxy URL (e.g. `http://127.0.0.1:8080`) |

### Format Presets

| Value | Description |
|---|---|
| `bestvideo*+bestaudio/best` | Best quality (default) |
| `bestvideo[height<=1080]+bestaudio/best[height<=1080]` | 1080p max |
| `bestvideo[height<=2160]+bestaudio/best[height<=2160]` | 4K max |
| `bestaudio/best` | Audio only |
| `worst` | Lowest quality |

### Output Template Examples

| Template | Result |
|---|---|
| `%(title)s.%(ext)s` | `My Video.mp4` |
| `%(uploader)s/%(title)s.%(ext)s` | `ChannelName/My Video.mp4` |
| `%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s` | `Playlist/01 - My Video.mp4` |

---

## How It Works

1. Copy a video URL -- FDM detects it
2. AvocadoDL runs yt-dlp to fetch available formats
3. FDM shows the formats in its download dialog
4. Pick a format -- FDM handles the download

---

## Updating

AvocadoDL checks for updates automatically: **Tools > Add-ons > select AvocadoDL > Check for updates**.

yt-dlp is auto-updated when `auto_update_ytdlp` is enabled (default).

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Python not found" | Install Python 3.8+ from [python.org](https://python.org) and restart FDM |
| "Unsupported URL" | The site isn't supported by yt-dlp yet |
| "Access denied (403)" or "Age-restricted" | Set `cookies_browser` in settings to your browser name |
| Formats not showing | Make sure `auto_update_ytdlp` is enabled (default) to keep yt-dlp current |
| Audio extraction fails | FDM bundles ffmpeg automatically -- if missing, install [ffmpeg](https://ffmpeg.org) |

## Building from Source

Requires: PowerShell, Python 3.8+, [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed via `pip install yt-dlp`

```powershell
.\build.ps1
```

---

## License

Public domain. See [LICENSE](LICENSE).
