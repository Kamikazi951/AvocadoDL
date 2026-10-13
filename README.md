# AvocadoDL FDM Add-on 1.1.0

Resolve video pages and streams with yt-dlp and let Free Download Manager choose formats and handle the download. Works with the AvocadoDL Chrome extension and the official FDM browser integration.

## Install or update

1. Open FDM → **Tools → Add-ons → Install from file**.
2. Select `avocadodl-1.1.0.fda` and restart FDM.
3. Keep the official Free Download Manager Chrome extension enabled.

Requires **Python 3.10+**. YouTube also needs **Deno 2.3.0+** (recommended) or **Node.js 22+**. The runner finds common Deno locations and enables Node when Deno is absent. FDM declares Deno as an add-on dependency; check its dependency setup if no JavaScript runtime is available. FDM handles final media processing.

The release bundles **yt-dlp 2026.08.19** and matching **yt-dlp-ejs 0.8.0**. These are the stable packages verified during this update. See the upstream [JavaScript runtime and EJS requirements](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

## What changed

- Bundle the YouTube JavaScript challenge solver alongside yt-dlp. Use current upstream extractor defaults instead of forcing a potentially incompatible player client.
- TikTok uses the maintained yt-dlp extractor. The previous unconditional third-party resolver is removed; video URLs are no longer sent to that extra service.
- Preserve cookie domain scope, path, security flags, session cookies and supported expiry representations.
- If Chrome cookie extraction fails because of a locked/encrypted database, retry a public video without browser cookies. Sign-in-only content still needs valid cookies.
- Preserve the provided user agent and referrer. Missing optional FDM proxy APIs no longer abort parsing.
- Share concurrent initialization, reload configuration after a minute, and avoid repeated browser probes. Handle null playlist items and malformed extractor output.
- Strip only the FDM marker from target URLs; leave signed query encoding intact. Proxy/referer URLs cannot be mistaken for the target video.
- Update yt-dlp and EJS together using PyPI SHA-256 verification, staged import validation and an atomic pointer to a new package directory. Failed/offline updates retain the working package; concurrent processes share an update lock. Checks are limited to once per hour, including failed checks.
- Select the newest bundled/cached package, avoiding downgrades from old caches. Do not print complete extraction JSON containing signed URLs or cookie headers to FDM's logs.

## Settings

Settings are created at `%APPDATA%\avocadodl\settings.json` on Windows, `~/Library/Application Support/avocadodl/settings.json` on macOS, and `$XDG_CONFIG_HOME/avocadodl/settings.json` (or `~/.config/avocadodl/settings.json`) on Linux.

Common options:

| Setting | Default | Purpose |
|---|---|---|
| `auto_update_ytdlp` | `true` | Check stable PyPI packages at most once per hour |
| `cookies_browser` | `""` | Browser supplied by FDM; set `chrome`, `edge`, `firefox`, etc. to override |
| `format` | `bestvideo*+bestaudio/best` | yt-dlp format selector |
| `extra_ytdlp_args` | `[]` | Additional string arguments |
| `proxy` | `""` | Proxy fallback when FDM supplies none |

The remaining existing options are listed in `settings.template.json`. This add-on runs yt-dlp to obtain metadata; FDM performs the actual download. Options for postprocessing, speed, subtitles or naming are not a guarantee that FDM implements the corresponding yt-dlp download behavior.

For a video requiring your signed-in session, FDM-provided cookies take priority. If browser cookie extraction is unavailable, use a Netscape-format cookies file you control, for example:

```json
"extra_ytdlp_args": ["--cookies", "C:\\Users\\YourName\\Downloads\\cookies.txt"]
```

Cookie files contain login credentials. Keep them private. AvocadoDL does not bypass DRM, account permissions, CAPTCHA, geographic restrictions or Chrome's cookie encryption.

## Troubleshooting

| Symptom | Check |
|---|---|
| No FDM dialog | Start FDM and enable its official Chrome extension; “FDM requested” is not native confirmation |
| Python missing | Install Python 3.10+ and restart FDM |
| YouTube lacks formats | Verify Deno/Node and the bundled EJS helper; keep updates enabled |
| 403 or login required | Open the video in your signed-in browser; check cookies/referrer; retry the page URL instead of an expired CDN link |
| Unsupported URL | Try the original video page; yt-dlp may not support this site |
| DRM protected | The add-on cannot download this content |

## Build and test

```powershell
.\build.ps1
python -m unittest discover -s tests -v
node --test tests/parser.cjs
```

The builder downloads current stable, verified pure-Python wheels into temporary staging; it does not install packages globally or delete a shared temporary directory. Future builds can contain newer yt-dlp/EJS versions than those checked above. Build with `python build.py` on other operating systems. `--offline` requires a complete `yt-dlp/` folder with both yt-dlp and its matching EJS package. The archive uses portable `/` paths and excludes bytecode caches. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development/release workflow and [CHANGELOG.md](CHANGELOG.md) for version notes.

Tests cover URL arguments, cookie errors, configuration validation, updater integrity/concurrency/rollback, FDM parser behavior, and the built archive's extraction of local direct media, HTML players, HLS and DASH. A live YouTube metadata check also succeeded during this update; that does not establish support for every site or account-restricted video.

## Release publishing

`update.json` intentionally continues to point to the existing published release. Upload the new `.fda` release asset before changing the public update manifest to 1.1.0. The local build does not publish a GitHub release or modify an installed FDM add-on.
