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


def _is_registered(name: str) -> bool:
    return any(f.name == name for f in fm.fontManager.ttflist)


def _ensure(name: str, base_url: str, files: list[str], fallback: str = _FALLBACK) -> str:
    if _is_registered(name):
        return name

    font_dir = os.path.join(os.path.dirname(__file__), "_fonts_cache")
    os.makedirs(font_dir, exist_ok=True)

    for fname in files:
        path = os.path.join(font_dir, fname)
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(base_url + fname, path)
            except Exception:
                _log.debug("Failed to download %s", fname, exc_info=True)
                continue
        try:
            fm.fontManager.addfont(path)
        except Exception:
            _log.debug("Failed to register font %s", fname, exc_info=True)

    return name if _is_registered(name) else fallback


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
