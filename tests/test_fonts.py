"""Font cache: an interrupted or bogus download must never poison the cache.

The network boundary (``urllib.request.urlretrieve``) is faked with matplotlib's
bundled DejaVu Sans as the "downloaded" font, and the font manager is swapped for
an empty one so registration starts from nothing.
"""

import logging
import shutil
import stat
import urllib.error
from pathlib import Path

import matplotlib.font_manager as fm
import pytest

from graphs import _fonts

_REAL_FONT = Path(fm.findfont("DejaVu Sans", fallback_to_default=False))
_FAMILY = "DejaVu Sans"
_FALLBACK = "Fallback Family"
_FNAME = "DejaVuSans.ttf"
_BASE_URL = "https://example.invalid/fonts/"


@pytest.fixture
def font_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An empty cache dir and an empty font manager, so nothing is pre-registered."""
    empty = fm.FontManager.__new__(fm.FontManager)
    empty.ttflist = []
    empty.afmlist = []
    monkeypatch.setattr(_fonts.fm, "fontManager", empty)
    monkeypatch.setattr(_fonts, "_FONT_DIR", str(tmp_path))
    return tmp_path


def _fake_network(
    monkeypatch: pytest.MonkeyPatch, payload: bytes, *, fail: bool = False
):
    """Make urlretrieve write *payload* to its target, then raise if *fail*."""
    calls: list[str] = []

    def urlretrieve(url: str, filename: str) -> None:
        calls.append(url)
        Path(filename).write_bytes(payload)
        if fail:
            raise urllib.error.URLError("connection reset mid-transfer")

    monkeypatch.setattr(_fonts.urllib.request, "urlretrieve", urlretrieve)
    return calls


def _ensure() -> str:
    return _fonts._ensure(_FAMILY, _BASE_URL, [_FNAME], _FALLBACK)


def test_successful_download_is_cached_and_registered(font_dir, monkeypatch, caplog):
    calls = _fake_network(monkeypatch, _REAL_FONT.read_bytes())

    with caplog.at_level(logging.WARNING, logger=_fonts.__name__):
        assert _ensure() == _FAMILY

    assert calls == [_BASE_URL + _FNAME]
    assert (font_dir / _FNAME).read_bytes() == _REAL_FONT.read_bytes()
    assert stat.S_IMODE((font_dir / _FNAME).stat().st_mode) == 0o644
    assert caplog.records == []


def test_interrupted_download_leaves_no_file_and_warns(font_dir, monkeypatch, caplog):
    half = _REAL_FONT.read_bytes()[: _REAL_FONT.stat().st_size // 2]
    _fake_network(monkeypatch, half, fail=True)

    with caplog.at_level(logging.WARNING, logger=_fonts.__name__):
        assert _ensure() == _FALLBACK

    assert list(font_dir.iterdir()) == []
    assert any(_FALLBACK in r.getMessage() for r in caplog.records)


def test_downloaded_non_font_is_rejected(font_dir, monkeypatch, caplog):
    _fake_network(monkeypatch, b"<!DOCTYPE html><html>captive portal</html>")

    with caplog.at_level(logging.WARNING, logger=_fonts.__name__):
        assert _ensure() == _FALLBACK

    assert list(font_dir.iterdir()) == []
    assert any(_FNAME in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize(
    "keep", [0, 100, 0.5, 0.99], ids=["empty", "header", "half", "tail"]
)
def test_truncated_cached_font_is_refetched(font_dir, monkeypatch, caplog, keep):
    data = _REAL_FONT.read_bytes()
    size = keep if isinstance(keep, int) else int(len(data) * keep)
    (font_dir / _FNAME).write_bytes(data[:size])
    calls = _fake_network(monkeypatch, data)

    with caplog.at_level(logging.WARNING, logger=_fonts.__name__):
        assert _ensure() == _FAMILY

    assert calls == [_BASE_URL + _FNAME]
    assert (font_dir / _FNAME).read_bytes() == data
    assert any("re-downloading" in r.getMessage() for r in caplog.records)


def test_complete_cached_font_is_not_refetched(font_dir, monkeypatch):
    shutil.copy(_REAL_FONT, font_dir / _FNAME)
    calls = _fake_network(monkeypatch, b"")

    assert _ensure() == _FAMILY
    assert calls == []


def test_completeness_check_accepts_real_font_and_rejects_truncation(tmp_path):
    data = _REAL_FONT.read_bytes()
    truncated = tmp_path / "truncated.ttf"
    truncated.write_bytes(data[:-1])

    assert _fonts._is_complete_font(str(_REAL_FONT))
    assert not _fonts._is_complete_font(str(truncated))
