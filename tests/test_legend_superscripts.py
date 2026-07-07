"""Legend entries: footnote-marker superscripts + anchor detection."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, footnotes, set_theme, top_legend
from graphs._superscript import _SUP_SCALE

MARKED = "Self-attributed*"
PLAIN = "Cross-attributed"


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _marked_legend_ax():
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([1, 2, 4], [0.6, 0.5, 0.4], label=MARKED)
    ax.plot([1, 2, 4], [0.6, 0.58, 0.55], label=PLAIN)
    return fig, ax


def _chunk(fig, text: str):
    matches = [t for t in fig.texts if t.get_text() == text]
    assert matches, f"no fig.text chunk {text!r} rendered"
    return matches[0]


def test_axes_legend_marker_superscripted_by_finalize():
    """A corner-legend entry's ``*`` re-renders as a raised, smaller chunk.

    The original entry text is kept (the legend box must not reflow and the
    anchor scan still needs the marker) but hidden via ``alpha=0``; the overlay
    renders the base text at full size and the marker at the superscript scale
    with a raised baseline.
    """
    fig, ax = _marked_legend_ax()
    legend = ax.legend(loc="upper right")
    finalize(ax, title="T", descriptor="D")

    entry = legend.get_texts()[0]
    assert entry.get_text() == MARKED  # text kept for layout + anchor scan
    assert entry.get_alpha() == 0.0  # inline full-size marker hidden

    base = _chunk(fig, "Self-attributed")
    star = _chunk(fig, "*")
    assert star.get_fontsize() == pytest.approx(entry.get_fontsize() * _SUP_SCALE)
    assert star.get_position()[1] > base.get_position()[1]  # raised baseline


def test_figure_top_legend_marker_superscripted():
    """The library's own ``top_legend`` (a figure legend) gets the same pass."""
    fig, ax = _marked_legend_ax()
    handles, labels = ax.get_legend_handles_labels()
    legend = top_legend(fig, handles, labels)
    finalize(ax, title="T", descriptor="D")

    entry = legend.get_texts()[0]
    assert entry.get_alpha() == 0.0
    star = _chunk(fig, "*")
    assert star.get_fontsize() == pytest.approx(entry.get_fontsize() * _SUP_SCALE)


def test_plain_legend_entries_untouched():
    """Entries without a marker keep their artist — no alpha, no overlay."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([1, 2], [0.6, 0.4], label=PLAIN)
    legend = ax.legend(loc="upper right")
    n_texts = len(fig.texts)
    finalize(ax, title="T", descriptor="D")

    entry = legend.get_texts()[0]
    assert entry.get_alpha() is None
    assert not any(t.get_text() == PLAIN for t in fig.texts[n_texts:])


def test_second_finalize_does_not_duplicate_overlay():
    """Processed entries are tagged; a repeated finalize adds no new chunks."""
    fig, ax = _marked_legend_ax()
    ax.legend(loc="upper right")
    finalize(ax, title="T", descriptor="D")
    n_star = sum(1 for t in fig.texts if t.get_text() == "*")
    finalize(ax, title="T", descriptor="D")
    assert sum(1 for t in fig.texts if t.get_text() == "*") == n_star == 1


def test_legend_anchor_silences_orphan_warning():
    """A ``*`` anchored only by a legend entry is not an orphan marker."""
    fig, ax = _marked_legend_ax()
    ax.legend(loc="upper right")
    finalize(ax, title="T", descriptor="D")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, "*Monitor told the transcript is its own output.")
    orphan = [w for w in caught if "no matching anchor" in str(w.message)]
    assert not orphan, [str(w.message) for w in orphan]


def test_orphan_warning_still_fires_without_any_anchor():
    """No anchor anywhere (legend included) still warns — the check kept teeth."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([1, 2], [0.6, 0.4], label=PLAIN)
    ax.legend(loc="upper right")
    finalize(ax, title="T", descriptor="D")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, "*A note with no referent on the chart.")
    orphan = [w for w in caught if "no matching anchor" in str(w.message)]
    assert orphan


def test_figure_legend_anchor_silences_orphan_warning():
    """A marker anchored only by a figure-level ``fig.legend`` entry is no orphan.

    ``check_anchors`` scans ``fig.legends`` as well as each axes' own legend —
    a bare ``fig.legend(...)`` label like ``"decline†"`` anchors ``†`` notes.
    """
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    (line,) = ax.plot([1, 2], [0.6, 0.4], label="decline†")
    fig.legend(handles=[line], loc="upper right")
    finalize(ax, title="T", descriptor="D")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, "†Definition of the starred decline.")
    orphan = [w for w in caught if "no matching anchor" in str(w.message)]
    assert not orphan, [str(w.message) for w in orphan]
