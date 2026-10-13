#!/usr/bin/env python3
"""Use current upstream extractors and fall back gracefully if browser cookies fail."""
import contextlib
import io
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ytdlp_helper import active_package_root


def configure_environment():
    candidates = [Path.home() / '.deno' / 'bin']
    if sys.platform == 'darwin':
        candidates += [Path('/opt/homebrew/bin'), Path('/usr/local/bin')]
    elif sys.platform == 'win32':
        candidates += [Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'deno',
                       Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'nodejs']
    paths = os.environ.get('PATH', '').split(os.pathsep)
    os.environ['PATH'] = os.pathsep.join([str(p) for p in candidates if p.is_dir() and str(p) not in paths] + paths)


def clean_url(value):
    parsed = urlsplit(value)
    # Preserve signed query encoding; remove only our integration marker.
    query = '&'.join(part for part in parsed.query.split('&')
                     if not part.lower().startswith('fdmguid='))
    return urlunsplit(parsed._replace(query=query))


def enhance_arguments(args):
    result = list(args)
    # FDM appends the target last, after options such as proxy/referer URLs.
    target = result[-1] if result and result[-1].startswith(('http://', 'https://')) else None
    if target:
        target = clean_url(target)
        result[-1] = target
    if not any(arg == '--js-runtimes' or arg.startswith('--js-runtimes=') or arg == '--no-js-runtimes' for arg in result):
        if not shutil.which('deno') and shutil.which('node'):
            result[0:0] = ['--js-runtimes', 'node']
    # Let the current extractor choose its supported YouTube clients.
    return target, result


def without_browser_cookies(args):
    result = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg == '--cookies-from-browser':
            skip = True
        elif not arg.startswith('--cookies-from-browser='):
            result.append(arg)
    return result


def execute(yt_dlp, args):
    errors = io.StringIO()
    with contextlib.redirect_stderr(errors):
        try:
            code = yt_dlp.main(args) or 0
        except SystemExit as error:
            code = error.code if isinstance(error.code, int) else (1 if error.code else 0)
    return code, errors.getvalue()


def main(args=None):
    configure_environment()
    root = active_package_root()
    if root:
        sys.path.insert(0, str(root))
    try:
        import yt_dlp
    except ImportError:
        sys.stderr.write('ERROR: yt-dlp is missing. Reinstall the AvocadoDL add-on.\n')
        return 1
    _, args = enhance_arguments(list(sys.argv[1:] if args is None else args))
    code, errors = execute(yt_dlp, args)
    # Chrome database locks / encryption must not block otherwise public videos.
    cookie_error = re.search(r'could not copy.*cookie|failed to decrypt|failed to load cookies|could not find.*cookies|cookie.*database|cookies?.*(?:decrypt|locked)', errors, re.I)
    fallback = without_browser_cookies(args)
    if code and cookie_error and fallback != args:
        code, errors = execute(yt_dlp, fallback)
        if code:
            errors += '\nERROR: Browser cookies could not be read. For sign-in-only videos, pass a Netscape cookie file using extra_ytdlp_args: ["--cookies", "path/to/cookies.txt"].\n'
    if errors:
        sys.stderr.write(errors)
    return code


if __name__ == '__main__':
    sys.exit(main())
