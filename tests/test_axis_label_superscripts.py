"""Axis-label footnote markers: superscript overlay stays anchored to its axis.

Regression tests for issue #14: a ``*``/``†`` marker inside an axis label
(``x_axis_label(ax, "harm load N*")``) is re-rendered as a superscript overlay
by ``finalize`` — but the overlay was anchored at fixed figure coordinates, so
a later ``footnotes()`` call (whose self-sizing band grows the bottom margin
and lifts the axes) left the label orphaned below the source row, off-figure.
"""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, footnotes, set_theme, x_axis_label
from graphs._superscript import _SUP_SCALE

MARKED_XLABEL = "harm load N*"
NOTE = "*Number of harmful artifacts in the probed transcript."
SOURCE = "Source: touchstone sweep"


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _marked_xlabel_fig():
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot([1, 2, 4, 8], [20, 17, 59, 41], marker="o")
    x_axis_label(ax, MARKED_XLABEL)
    return fig, ax


def _fig_bbox(fig, artist):
    renderer = fig.canvas.get_renderer()
    return artist.get_window_extent(renderer=renderer).transformed(
        fig.transFigure.inverted()
    )


def _chunks(fig, text: str):
    return [t for t in fig.texts if t.get_text() == text]


def test_xlabel_marker_superscripted_by_finalize():
    """The ``*`` re-renders as a raised, smaller chunk; the base text at full size.

    The native xlabel artist keeps its text (the footnote anchor scan and the
    bottom-band measurement need its extent) but is hidden via ``alpha=0`` —
    the same contract as legend-entry superscripts.
    """
    fig, ax = _marked_xlabel_fig()
    finalize(ax, title="T", descriptor="D", source="")

    label = ax.xaxis.label
    assert label.get_text() == MARKED_XLABEL  # kept for layout + anchor scan
    assert label.get_alpha() == 0.0  # inline full-size marker hidden

    (base,) = _chunks(fig, "harm load N")
    (star,) = _chunks(fig, "*")
    assert star.get_fontsize() == pytest.approx(label.get_fontsize() * _SUP_SCALE)
    fig.canvas.draw()
    assert _fig_bbox(fig, star).y0 > _fig_bbox(fig, base).y0  # raised baseline


def test_marked_xlabel_stays_anchored_above_footnote_band():
    """The issue #14 repro: marked xlabel + one footnote + finalize.

    ``footnotes()``'s self-sizing band grows the bottom margin after the
    overlay is drawn; the overlay must ride up with the axes — below the axes
    baseline, above every footnote/source row, and on-figure — instead of
    being orphaned under the source row.
    """
    fig, ax = _marked_xlabel_fig()
    finalize(ax, title="T", descriptor="D", source="")
    footnotes(fig, NOTE, source=SOURCE)
    fig.canvas.draw()

    # The footnote row starts with its own superscripted "*", so pick the
    # xlabel's star by adjacency: the "*" chunk that continues the base
    # chunk's row (the footnote's star sits on a different row entirely).
    (base,) = _chunks(fig, "harm load N")
    base_bb = _fig_bbox(fig, base)
    stars = [
        t
        for t in _chunks(fig, "*")
        if _fig_bbox(fig, t).y0 < base_bb.y1 and _fig_bbox(fig, t).y1 > base_bb.y0
    ]
    assert len(stars) == 1, "expected exactly one star on the xlabel's row"
    overlay = [base, *stars]
    overlay_bbs = [_fig_bbox(fig, t) for t in overlay]
    label_top = max(bb.y1 for bb in overlay_bbs)
    label_bottom = min(bb.y0 for bb in overlay_bbs)

    # On-figure: the orphaned label rendered at y<0 before the fix.
    assert label_bottom >= 0.0, (
        f"xlabel overlay fell off the figure (bottom at y={label_bottom:.4f})"
    )

    # Anchored to its axis: below the axes baseline...
    axes_bottom = ax.get_position().y0
    assert label_top <= axes_bottom + 1e-3, (
        f"xlabel overlay (top y={label_top:.4f}) not below the axes "
        f"baseline (y={axes_bottom:.4f})"
    )

    # ...and above every footnote/source row (before the fix it sat below them).
    row_texts = [
        t
        for t in fig.texts
        if t.get_text().strip()
        and t not in overlay
        and ("Number of harmful" in t.get_text() or "touchstone" in t.get_text())
    ]
    assert row_texts, "footnote/source rows missing"
    rows_top = max(_fig_bbox(fig, t).y1 for t in row_texts)
    assert label_bottom >= rows_top - 1e-3, (
        f"xlabel overlay (bottom y={label_bottom:.4f}) orphaned below the "
        f"footnote band (top y={rows_top:.4f})"
    )


def test_xlabel_anchor_silences_orphan_warning():
    """A ``*`` anchored only by the xlabel is not an orphan marker.

    Before the fix ``finalize`` wiped the xlabel text, so ``footnotes``'s
    anchor scan could no longer find the marker and warned spuriously.
    """
    fig, ax = _marked_xlabel_fig()
    finalize(ax, title="T", descriptor="D", source="")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, NOTE, source=SOURCE)
    orphan = [w for w in caught if "no matching anchor" in str(w.message)]
    assert not orphan, [str(w.message) for w in orphan]


def test_second_finalize_does_not_duplicate_overlay():
    """Processed labels are tagged; a repeated finalize adds no new chunks."""
    fig, ax = _marked_xlabel_fig()
    finalize(ax, title="T", descriptor="D", source="")
    n_star = len(_chunks(fig, "*"))
    finalize(ax, title="T", descriptor="D", source="")
    assert len(_chunks(fig, "*")) == n_star == 1


def test_plain_xlabel_untouched():
    """No marker ⇒ the native artist keeps rendering — no alpha, no overlay."""
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    ax.plot([1, 2, 4], [20, 17, 59])
    x_axis_label(ax, "harm load N")
    finalize(ax, title="T", descriptor="D", source="")

    label = ax.xaxis.label
    assert label.get_text() == "harm load N"
    assert label.get_alpha() is None
    assert not _chunks(fig, "harm load N")
