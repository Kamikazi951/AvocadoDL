# Contributing

Thanks for helping make AvocadoDL better!

## How to Help

- **Report bugs** -- Open an issue with the video URL and error message
- **Suggest features** -- Open an issue describing your idea
- **Submit fixes** -- PRs welcome for bug fixes and improvements

## Development

```powershell
.\build.ps1
```

Test by installing the built `.fda` in FDM: **Tools > Add-ons > Install from file**.

## Code Style

- JS files use ES5 (FDM's engine is not Node.js)
- Python files target 3.8+
- No external dependencies beyond yt-dlp

## Releasing

1. Update version in `manifest.json`
2. Tag the release (`git tag vX.Y.Z`)
3. GitHub Actions builds and publishes the `.fda` automatically
