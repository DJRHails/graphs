"""Shared CSV loader for the example scripts.

Fetches each CSV from its source URL the first time it's seen and caches
the response under ``examples/.data/``. Subsequent runs read from cache.
The cache directory is gitignored — it's a build artefact, not source.
"""

from __future__ import annotations

import io
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

CACHE_DIR = Path(__file__).resolve().parent / ".data"


def load_csv_text(url: str) -> str:
    """Return the CSV body for ``url``, fetching once and caching to disk."""
    CACHE_DIR.mkdir(exist_ok=True)
    name = Path(urlparse(url).path).name
    cached = CACHE_DIR / name
    if cached.exists():
        return cached.read_text(encoding="utf-8")
    with urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    cached.write_text(text, encoding="utf-8")
    return text


def load_csv_lines(url: str) -> io.StringIO:
    """Return a StringIO over the CSV body, ready for ``csv.reader``."""
    return io.StringIO(load_csv_text(url))
