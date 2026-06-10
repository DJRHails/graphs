"""Title/descriptor auto-wrap in finalize()."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme
from graphs._finalize import TITLE_SIZE_PT, TITLE_WEIGHT, _wrap_to_fig_width
from graphs._fonts import _get_font


@pytest.fixture
def fig():
    set_theme()
    fig = plt.figure(figsize=(4.0, 3.0))
    yield fig
    plt.close(fig)


def _title_fp() -> fm.FontProperties:
    return fm.FontProperties(
        family=_get_font(), weight=TITLE_WEIGHT, size=TITLE_SIZE_PT
    )


def test_wrap_breaks_overflowing_line(fig):
    text = "A more complex arms race than that of the cold war looms"
    wrapped = _wrap_to_fig_width(
        fig, text, fontproperties=_title_fp(), avail_fig_w=0.94
    )
    assert "\n" in wrapped
    assert wrapped.replace("\n", " ") == text


def test_wrap_keeps_short_line_intact(fig):
    wrapped = _wrap_to_fig_width(
        fig, "Short title", fontproperties=_title_fp(), avail_fig_w=0.94
    )
    assert wrapped == "Short title"


def test_wrap_preserves_explicit_breaks(fig):
    text = "World Christian population\n% of total"
    wrapped = _wrap_to_fig_width(
        fig, text, fontproperties=_title_fp(), avail_fig_w=0.94
    )
    assert wrapped == text


def test_wrap_avoids_single_word_widow(fig):
    text = "Sub-Saharan Africa is the biggest area of expansion for Christianity"
    wrapped = _wrap_to_fig_width(
        fig, text, fontproperties=_title_fp(), avail_fig_w=0.94
    )
    assert "\n" in wrapped
    for line in wrapped.split("\n"):
        assert " " in line, f"single-word widow line: {line!r}"
    assert wrapped.replace("\n", " ") == text


def test_finalize_wraps_long_title_to_figure_width(fig):
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(
        ax,
        title="A more complex arms race than that of the cold war looms",
        descriptor="Estimated nuclear-warhead inventories, Oct 2025",
    )
    title_artists = [
        t for t in fig.texts if "arms race" in t.get_text().replace("\n", " ")
    ]
    assert title_artists, "title text artist not found"
    assert "\n" in title_artists[0].get_text()
