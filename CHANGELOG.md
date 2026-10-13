# Changelog

## 1.1.0 — pending release

### Fixed
- Include yt-dlp's matching EJS helper so YouTube extraction can use a supported JavaScript runtime.
- Preserve signed URL encoding, referrers, user agents and cookie scope. Retry public extraction without browser cookies when Chrome's cookie database is unavailable.
- Share parser initialization, refresh configuration, tolerate missing optional proxy APIs and handle deleted playlist entries or malformed extractor output.
- Verify dependency hashes and imports before atomically activating updates. Failed or offline updates retain the working package; concurrent checks share a lock.
- Prevent older cached packages from replacing newer bundled versions.

### Changed
- Use maintained upstream extractor defaults instead of forced YouTube clients or an unconditional third-party TikTok resolver.
- Avoid logging full extractor JSON containing signed URLs and cookie headers.
- Build portable archives with standard-library Python tooling, verified dependencies and no bytecode caches. Windows builds retain a PowerShell wrapper.

### Verification
- Python runtime/updater tests, JavaScript parser tests and packaged extraction fixtures for direct media, HTML players, HLS and DASH run in GitHub Actions.
- The locally checked build contains yt-dlp 2026.08.19 and yt-dlp-ejs 0.8.0. The builder resolves current stable packages and their matching EJS version; future builds may contain newer dependencies.
- A live YouTube metadata check succeeded. Native FDM download completion and every website/account restriction are outside the automated coverage.

The public update manifest still points to the existing published release. Update it only after the new release asset has been uploaded and verified.
