"""Title/descriptor auto-wrap in finalize()."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import pytest

from graphs import finalize, footnotes, set_theme
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


def _descriptor_artists(fig, fragment: str):
    return [t for t in fig.texts if fragment in t.get_text().replace("\n", " ")]


def test_autowrapped_descriptor_stays_normal_weight(fig):
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(
        ax,
        title="Short",
        descriptor=(
            "Estimated nuclear-warhead inventories across all declared "
            "and undeclared states, October 2025"
        ),
    )
    artists = _descriptor_artists(fig, "inventories")
    assert artists, "descriptor text artist not found"
    assert "\n" in artists[0].get_text(), "expected the descriptor to wrap"
    for t in artists:
        assert t.get_fontproperties().get_weight() == "normal"


def test_explicit_break_descriptor_gets_semibold_lead(fig):
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(
        ax,
        title="Short",
        descriptor="World Christian population\n% of total",
    )
    (lead,) = _descriptor_artists(fig, "World Christian population")
    (rest,) = _descriptor_artists(fig, "% of total")
    assert lead.get_fontproperties().get_weight() == "semibold"
    assert rest.get_fontproperties().get_weight() == "normal"


def test_wrapped_lead_segment_is_fully_semibold(fig):
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(
        ax,
        title="Short",
        descriptor=(
            "Estimated nuclear-warhead inventories across all declared "
            "and undeclared states\n% of total"
        ),
    )
    (lead,) = _descriptor_artists(fig, "inventories")
    (rest,) = _descriptor_artists(fig, "% of total")
    assert "\n" in lead.get_text(), "expected the lead segment to wrap"
    assert lead.get_fontproperties().get_weight() == "semibold"
    assert rest.get_fontproperties().get_weight() == "normal"


_LONG_SOURCE = (
    "Sources: OR-Bench-toxic; StrongREJECT; HarmBench; OpenAI-Moderation; WMDP; "
    "harm_mismatch_eval.py · relabelled by Claude Opus 4.8 · "
    "N=300 harmful, 120 benign"
)


def test_footnotes_wraps_over_wide_source(fig):
    """An over-wide source line word-wraps to fit the figure, like the notes do."""
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(ax, title="Short", descriptor="Some metric", source="", footnote_lines=1)
    footnotes(fig, source=_LONG_SOURCE, verify=False)
    # The wrapped source becomes a single newline-bearing artist (no markers/URLs).
    src_artists = [t for t in fig.texts if "OR-Bench-toxic" in t.get_text()]
    assert src_artists, "source text artist not found"
    assert "\n" in src_artists[0].get_text(), "expected the over-wide source to wrap"


def test_footnotes_wrapped_source_stays_within_figure(fig):
    """After wrapping, the source artist no longer runs past the figure's right edge.

    Without the wrap the single-line source spills past x=1; the wrap keeps every
    source line inside the figure width (a small antialiasing tolerance aside).
    """
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(ax, title="Short", descriptor="Some metric", source="", footnote_lines=1)
    footnotes(fig, source=_LONG_SOURCE, verify=False)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    (src,) = [t for t in fig.texts if "OR-Bench-toxic" in t.get_text()]
    right = src.get_window_extent(renderer=renderer).transformed(inv).x1
    assert right <= 1.005, (
        f"wrapped source still overflows the figure width: x1={right:.3f}"
    )


def test_footnotes_short_source_stays_single_line(fig):
    """A source that fits is not wrapped — regression guard for the common case."""
    ax = fig.add_subplot()
    ax.plot([0, 1], [0, 1])
    finalize(ax, title="Short", descriptor="Some metric", source="")
    footnotes(fig, source="Source: harm_mismatch_eval.py", verify=False)
    (src,) = [t for t in fig.texts if "harm_mismatch_eval.py" in t.get_text()]
    assert "\n" not in src.get_text(), "short source should not wrap"
