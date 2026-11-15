"""Resolve local fonts once, avoiding repeated WebKit/Fontconfig family scans."""

from functools import lru_cache
import json
from pathlib import Path
import shutil
import subprocess


@lru_cache(maxsize=1)
def local_font_css():
    if not shutil.which("fc-match"):
        return ""
    rules = []
    families = [
        ("Preview Sans", "sans-serif", "normal", 400),
        ("Preview Sans", "sans-serif:weight=bold", "normal", 700),
        ("Preview Sans", "sans-serif:slant=italic", "italic", 400),
        ("Preview Sans", "sans-serif:weight=bold:slant=italic", "italic", 700),
        ("Preview Mono", "monospace", "normal", 400),
        ("Preview Mono", "monospace:weight=bold", "normal", 700),
        ("Preview Emoji", "emoji", "normal", 400),
    ]
    for name, pattern, style, weight in families:
        try:
            match = subprocess.run(
                ["fc-match", "-f", "%{file}", pattern],
                capture_output=True,
                text=True,
                check=True,
                timeout=1,
            ).stdout
            path = Path(match)
            if not path.is_file() or path.suffix.lower() not in (
                ".ttf",
                ".otf",
                ".woff",
                ".woff2",
            ):
                continue
        except (OSError, subprocess.SubprocessError):
            continue
        rules.append(
            f'@font-face {{ font-family: "{name}"; font-style: {style}; '
            f"font-weight: {weight}; font-display: swap; src: url({json.dumps(path.as_uri())}); }}"
        )
    return "\n".join(rules)
