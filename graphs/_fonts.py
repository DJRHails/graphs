"""IBM Plex font management for matplotlib.

Downloads font files from github.com/IBM/plex only when the fonts are not
already registered. We load three families of the one superfamily:

* **IBM Plex Sans** — used for the chart headline (Bold).
* **IBM Plex Sans Condensed** — used for subtitle, ticks, labels, and source
  (styleguide rule: everything except the headline is condensed).
* **IBM Plex Mono** — literal tokens, code and prompts
  (``fontfamily="monospace"``), so a literal reads as a literal.
"""

import logging
import os
import struct
import tempfile
import urllib.request

import matplotlib.font_manager as fm

_log = logging.getLogger(__name__)

_IBM_SANS_BASE = (
    "https://github.com/IBM/plex/raw/master/"
    "packages/plex-sans/fonts/complete/ttf/"
)
_IBM_SANS_FILES = [
    "IBMPlexSans-Regular.ttf",
    "IBMPlexSans-Bold.ttf",
    "IBMPlexSans-SemiBold.ttf",
    "IBMPlexSans-Light.ttf",
    "IBMPlexSans-Italic.ttf",
]
_IBM_COND_BASE = (
    "https://github.com/IBM/plex/raw/master/"
    "packages/plex-sans-condensed/fonts/complete/ttf/"
)
_IBM_COND_FILES = [
    "IBMPlexSansCondensed-Regular.ttf",
    "IBMPlexSansCondensed-Medium.ttf",
    "IBMPlexSansCondensed-Bold.ttf",
    "IBMPlexSansCondensed-Light.ttf",
]

_IBM_MONO_BASE = (
    "https://github.com/IBM/plex/raw/master/"
    "packages/plex-mono/fonts/complete/ttf/"
)
_IBM_MONO_FILES = [
    "IBMPlexMono-Regular.ttf",
    "IBMPlexMono-Medium.ttf",
    "IBMPlexMono-Bold.ttf",
]

_SANS_NAME = "IBM Plex Sans"
_COND_NAME = "IBM Plex Sans Condensed"
_MONO_NAME = "IBM Plex Mono"
_FALLBACK = "DejaVu Sans"
_FALLBACK_MONO = "DejaVu Sans Mono"


_FONT_DIR = os.path.join(os.path.dirname(__file__), "_fonts_cache")

# sfnt (TrueType/OpenType) layout: a 12-byte header, then a 16-byte record per table.
_SFNT_HEADER = struct.Struct(">4sH6x")  # sfntVersion, numTables, (search fields)
_SFNT_TABLE = struct.Struct(">4x4xII")  # (tag), (checksum), offset, length
_SFNT_VERSIONS = (b"\x00\x01\x00\x00", b"true", b"OTTO")


def _is_registered(name: str) -> bool:
    return any(f.name == name for f in fm.fontManager.ttflist)


def _is_complete_font(path: str) -> bool:
    """Whether *path* is an sfnt font whose every declared table lies inside the file.

    FreeType (and so matplotlib) opens a truncated TTF without complaint as long as
    its header survived, so loading the font cannot detect an interrupted download.
    """
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) < _SFNT_HEADER.size:
        return False
    version, num_tables = _SFNT_HEADER.unpack_from(data)
    directory_end = _SFNT_HEADER.size + num_tables * _SFNT_TABLE.size
    if version not in _SFNT_VERSIONS or num_tables == 0 or len(data) < directory_end:
        return False
    for i in range(num_tables):
        record_start = _SFNT_HEADER.size + i * _SFNT_TABLE.size
        offset, length = _SFNT_TABLE.unpack_from(data, record_start)
        if offset + length > len(data):
            return False
    return True


def _download(url: str, path: str) -> None:
    """Fetch *url* to *path* atomically: a partial or non-font body never lands."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".part")
    os.close(fd)
    try:
        # mkstemp creates 0600; the cache is shared by every user of this install.
        os.chmod(tmp, 0o644)
        urllib.request.urlretrieve(url, tmp)
        if not _is_complete_font(tmp):
            raise ValueError(f"{url} did not return a complete TrueType font")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _cached_font(base_url: str, fname: str) -> str:
    """Return the path to a complete cached copy of *fname*, downloading if needed."""
    path = os.path.join(_FONT_DIR, fname)
    if os.path.exists(path):
        if _is_complete_font(path):
            return path
        _log.warning("Cached font %s is incomplete or corrupt; re-downloading", path)
    _download(base_url + fname, path)
    return path


def _ensure(name: str, base_url: str, files: list[str], fallback: str = _FALLBACK) -> str:
    if _is_registered(name):
        return name

    os.makedirs(_FONT_DIR, exist_ok=True)
    failures: list[str] = []
    for fname in files:
        try:
            fm.fontManager.addfont(_cached_font(base_url, fname))
        except Exception as exc:  # noqa: BLE001 - every failure is reported below
            failures.append(f"{fname}: {exc}")

    resolved = name if _is_registered(name) else fallback
    if failures or resolved != name:
        _log.warning(
            "Could not load %d of %d %s font files (%s); using %s",
            len(failures),
            len(files),
            name,
            "; ".join(failures) or "family not registered",
            resolved,
        )
    return resolved


def ensure_ibm_plex() -> str:
    """Return the IBM Plex Sans family name (download if missing)."""
    return _ensure(_SANS_NAME, _IBM_SANS_BASE, _IBM_SANS_FILES)


def ensure_ibm_plex_condensed() -> str:
    """Return the IBM Plex Sans Condensed family name (download if missing)."""
    return _ensure(_COND_NAME, _IBM_COND_BASE, _IBM_COND_FILES)


def ensure_ibm_plex_mono() -> str:
    """Return the IBM Plex Mono family name (download if missing)."""
    return _ensure(_MONO_NAME, _IBM_MONO_BASE, _IBM_MONO_FILES, _FALLBACK_MONO)


_FONT_SANS: str = ""
_FONT_COND: str = ""
_FONT_MONO: str = ""


def _get_font() -> str:
    global _FONT_SANS  # noqa: PLW0603
    if not _FONT_SANS:
        _FONT_SANS = ensure_ibm_plex()
    return _FONT_SANS


def _get_font_condensed() -> str:
    global _FONT_COND  # noqa: PLW0603
    if not _FONT_COND:
        _FONT_COND = ensure_ibm_plex_condensed()
    return _FONT_COND


def _get_font_mono() -> str:
    global _FONT_MONO  # noqa: PLW0603
    if not _FONT_MONO:
        _FONT_MONO = ensure_ibm_plex_mono()
    return _FONT_MONO
