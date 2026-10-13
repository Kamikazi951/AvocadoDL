# Contributing

Thanks for helping make AvocadoDL better!

## How to Help

- **Report bugs** -- Open an issue with the video URL and error message
- **Suggest features** -- Open an issue describing your idea
- **Submit fixes** -- PRs welcome for bug fixes and improvements

## Development

```powershell
.\build.ps1
python -m unittest discover -s tests -v
node --test tests/parser.cjs
```

Use Python 3.10+ and Node.js 22+ for development. On macOS/Linux, replace the PowerShell build command with `python build.py`. The builder downloads verified yt-dlp and matching EJS wheels into temporary staging. Package tests require the built `.fda` and use local media fixtures.

Also test by installing the built `.fda` in FDM: **Tools > Add-ons > Install from file**. Keep generated packages, exported cookies and local configuration out of commits.

## Code Style

- JS files use ES5 (FDM's engine is not Node.js)
- Python files target 3.10+
- Python build/update tooling uses the standard library; the add-on bundles yt-dlp and yt-dlp-ejs

## Releasing

1. Update the version in `manifest.json` and the user-facing changelog.
2. Build and run all tests, then commit and push the changes.
3. Tag the tested commit (`git tag -a vX.Y.Z -m "Release X.Y.Z"`) and push that tag.
4. Publish the corresponding GitHub release. The release event builds, tests and uploads `avocadodl.fda`; pushing a tag alone only produces a workflow artifact.
5. Verify the uploaded asset before updating `update.json` to its version and release URL. Never advertise an asset that is not available yet.
