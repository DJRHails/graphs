"""Bottom band reserves room for the x-axis label, in both call orders.

``finalize`` places the source line beneath the axes and *measures*
``ax.xaxis.label`` when choosing its depth — but the auto-padding
(`_compute_auto_pads`) historically reserved room only for the x-tick
labels, never the xlabel. Consequences this file guards against:

* an ``x_axis_label`` set *before* ``finalize`` pushed the source line
  off-canvas (the measured placement descended below the label into room
  that was never reserved);
* an ``x_axis_label`` set *after* ``finalize`` painted directly on top of
  the already-drawn source line.

Both orders must now produce the same layout, with the label and the
source line fully on-canvas and clear of each other.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, x_axis_label

SOURCE = "Source: Touchstone rollouts"
XLABEL = "Sweep budget, samples per monitor"


@pytest.fixture(autouse=True)
def _theme():
    set_theme()


def _fig_bbox(fig, artist):
    """Rendered bbox of ``artist`` in figure coordinates."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    return artist.get_window_extent(renderer=renderer).transformed(
        fig.transFigure.inverted()
    )


def _source_artists(fig):
    """The figure texts carrying the source line (superscript-chunk safe)."""
    return [t for t in fig.texts if SOURCE.split()[0] in t.get_text()]


def _source_bbox(fig):
    artists = _source_artists(fig)
    assert artists, "source line was not rendered"
    boxes = [_fig_bbox(fig, t) for t in artists]
    from matplotlib.transforms import Bbox

    return Bbox.union(boxes)


def _labelled_chart(*, label_when: str):
    """A line chart with a source line; xlabel set before or after finalize."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    if label_when == "before":
        x_axis_label(ax, XLABEL)
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall\n% of attack transcripts flagged",
        source=SOURCE,
    )
    if label_when == "after":
        x_axis_label(ax, XLABEL)
    return fig, ax


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_xlabel_and_source_do_not_overlap(label_when):
    """The xlabel band and the source line must not intersect vertically."""
    fig, ax = _labelled_chart(label_when=label_when)
    label_bb = _fig_bbox(fig, ax.xaxis.label)
    source_bb = _source_bbox(fig)
    assert label_bb.y0 > source_bb.y1, (
        f"x-axis label (y0={label_bb.y0:.3f}) overlaps the source line "
        f"(y1={source_bb.y1:.3f}) when the label is set {label_when} finalize"
    )
    plt.close(fig)


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_xlabel_and_source_stay_on_canvas(label_when):
    """Neither the label nor the source line may fall below the figure edge."""
    fig, ax = _labelled_chart(label_when=label_when)
    label_bb = _fig_bbox(fig, ax.xaxis.label)
    source_bb = _source_bbox(fig)
    assert label_bb.y0 >= 0.0, (
        f"x-axis label bottom at y={label_bb.y0:.3f} is off-canvas "
        f"(label set {label_when} finalize)"
    )
    assert source_bb.y0 >= 0.0, (
        f"source line bottom at y={source_bb.y0:.3f} is off-canvas "
        f"(label set {label_when} finalize)"
    )
    plt.close(fig)


def test_xlabel_call_order_is_layout_invariant():
    """Setting the xlabel before vs after finalize gives the same layout."""
    fig_a, ax_a = _labelled_chart(label_when="before")
    fig_b, ax_b = _labelled_chart(label_when="after")

    pos_a, pos_b = ax_a.get_position(), ax_b.get_position()
    for name, va, vb in (
        ("axes bottom", pos_a.y0, pos_b.y0),
        ("axes top", pos_a.y1, pos_b.y1),
    ):
        assert abs(va - vb) < 2e-3, f"{name} differs between orders: {va:.4f} vs {vb:.4f}"

    label_a = _fig_bbox(fig_a, ax_a.xaxis.label)
    label_b = _fig_bbox(fig_b, ax_b.xaxis.label)
    assert abs(label_a.y0 - label_b.y0) < 2e-3, (
        f"xlabel position differs between orders: {label_a.y0:.4f} vs {label_b.y0:.4f}"
    )

    source_a = _source_bbox(fig_a)
    source_b = _source_bbox(fig_b)
    assert abs(source_a.y0 - source_b.y0) < 2e-3, (
        f"source position differs between orders: "
        f"{source_a.y0:.4f} vs {source_b.y0:.4f}"
    )
    plt.close(fig_a)
    plt.close(fig_b)


def test_unlabelled_layout_unchanged_reference():
    """A figure with no xlabel keeps the pre-fix geometry (regression pin).

    Guards the no-xlabel path against any global vertical shift: the bottom
    reservation must be driven purely by the tick band and source constants,
    exactly as before the xlabel band was added.
    """
    from graphs._finalize import (
        AUTO_LAYOUT_BOTTOM_MARGIN,
        SOURCE_SIZE_PT,
        SOURCE_TICK_CLEARANCE,
        SOURCE_Y_OFFSET,
        _xtick_band_height_fig,
    )

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall\n% of attack transcripts flagged",
        source=SOURCE,
    )
    fig.canvas.draw()
    tick_band = _xtick_band_height_fig(fig, ax)
    source_depth = max(SOURCE_Y_OFFSET, tick_band + SOURCE_TICK_CLEARANCE)
    expected_bottom = (
        source_depth
        + SOURCE_SIZE_PT / 72.0 / fig.get_figheight()
        + AUTO_LAYOUT_BOTTOM_MARGIN
    )
    assert abs(ax.get_position().y0 - expected_bottom) < 1e-6
    plt.close(fig)
