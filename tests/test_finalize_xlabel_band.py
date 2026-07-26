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


def test_non_anchor_panel_label_clears_source_in_both_orders():
    """A late label on a lowest-row panel that is NOT the finalize anchor.

    The band re-opening must key off the figure's record, not the anchor
    axes identity, and the source scan must cover the whole lowest row —
    previously the late call was a silent no-op and the label painted
    straight through the source line.
    """

    def chart(label_when):
        fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.4))
        for panel in axes:
            panel.plot([0, 1, 2, 3], [10, 30, 25, 40])
        if label_when == "before":
            x_axis_label(axes[1], XLABEL)
        finalize(
            axes[0],
            title="Recall rises with sweep budget",
            descriptor="Monitor recall\n% of attack transcripts flagged",
            source=SOURCE,
        )
        if label_when == "after":
            x_axis_label(axes[1], XLABEL)
        return fig, axes

    results = {}
    for when in ("before", "after"):
        fig, axes = chart(when)
        label_bb = _fig_bbox(fig, axes[1].xaxis.label)
        source_bb = _source_bbox(fig)
        assert label_bb.y0 > source_bb.y1, (
            f"non-anchor xlabel (y0={label_bb.y0:.3f}) overlaps the source "
            f"(y1={source_bb.y1:.3f}) when set {when} finalize"
        )
        assert source_bb.y0 >= 0.0
        results[when] = (label_bb.y0, source_bb.y0)
        plt.close(fig)

    for a, b in zip(results["before"], results["after"]):
        assert abs(a - b) < 2e-3, (
            f"non-anchor layouts differ between orders: {results}"
        )


def test_multirow_late_label_warns_when_source_leaves_canvas():
    """Multi-row grids cannot re-grow the bottom band post hoc.

    The source still moves clear of the late label; when that pushes it off
    the canvas the caller must be told (the silent version clipped the
    source line out of a plain ``savefig``).
    """
    fig, axes = plt.subplots(2, 1, figsize=(5.0, 3.4))
    for panel in axes:
        panel.plot([0, 1, 2, 3], [10, 30, 25, 40])
    finalize(
        axes[1],
        title="Recall rises with sweep budget",
        descriptor="Monitor recall",
        source=SOURCE,
    )
    with pytest.warns(UserWarning, match="multi-row"):
        x_axis_label(axes[1], XLABEL)
    label_bb = _fig_bbox(fig, axes[1].xaxis.label)
    source_bb = _source_bbox(fig)
    assert label_bb.y0 > source_bb.y1, "source was not re-seated below the label"
    plt.close(fig)


def test_late_label_above_lowest_row_warns():
    """A late label on an upper-row panel needs hspace, which is settled."""
    fig, axes = plt.subplots(2, 1, figsize=(5.0, 3.4))
    for panel in axes:
        panel.plot([0, 1, 2, 3], [10, 30, 25, 40])
    finalize(axes[0], title="Recall rises with sweep budget", source=SOURCE)
    with pytest.warns(UserWarning, match="lowest row"):
        x_axis_label(axes[0], XLABEL)
    plt.close(fig)


def test_late_label_warns_on_footnotes_band_intrusion():
    """A ``footnotes()``-drawn band is invisible to the finalize record."""
    from graphs import footnotes

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall",
    )
    footnotes(fig, source=SOURCE)
    with pytest.warns(UserWarning, match="footnotes"):
        x_axis_label(ax, "Sweep budget\nsamples per monitor")
    plt.close(fig)


def test_on_grid_ylabels_match_between_orders():
    """The post-hoc shrink must not leave stale frozen y labels behind.

    ``finalize`` freezes the y tick labels into ``y-labels-on-grid``
    artists; shrinking the axes afterwards re-derives the y locator, so
    without a re-application the after-order chart keeps a denser label set
    than the gridlines underneath it.
    """

    def frozen_labels(label_when):
        fig, ax = plt.subplots(figsize=(5.0, 2.6))
        ax.bar(range(5), [3, 5, 2, 6, 4])
        ax.set_xticks(range(5))
        ax.set_xticklabels(
            ["forced", "calibrated", "audited", "unmonitored", "baseline"],
            rotation=40,
            ha="right",
        )
        if label_when == "before":
            x_axis_label(ax, "Sweep budget\nsamples per monitor")
        finalize(
            ax,
            title="Recall rises with sweep budget",
            descriptor="Monitor recall",
            source=SOURCE,
        )
        if label_when == "after":
            x_axis_label(ax, "Sweep budget\nsamples per monitor")
        fig.canvas.draw()
        labels = sorted(
            t.get_text()
            for t in ax.texts
            if t.get_gid() == "y-labels-on-grid" and t.get_text()
        )
        plt.close(fig)
        return labels

    before, after = frozen_labels("before"), frozen_labels("after")
    assert before == after, (
        f"frozen on-grid y labels differ between orders: {before} vs {after}"
    )


def test_hidden_ticklabels_band_still_clears_margin():
    """Outward ticks without labels: the label seats below the spine+ticks.

    matplotlib seats the xlabel below the union of tick-label bboxes and
    the bottom spine extent (which includes drawn ticks); reserving from
    the bare baseline under-reserved by the tick length and the source
    consumed the breathing margin.
    """
    from graphs._finalize import AUTO_LAYOUT_BOTTOM_MARGIN

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    ax.tick_params(axis="x", labelbottom=False)
    x_axis_label(ax, XLABEL)
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall",
        source=SOURCE,
    )
    source_bb = _source_bbox(fig)
    assert source_bb.y0 >= AUTO_LAYOUT_BOTTOM_MARGIN - 5e-3, (
        f"source bottom at y={source_bb.y0:.4f} ate into the breathing margin"
    )
    plt.close(fig)


def test_label_shrink_after_finalize_keeps_source_seated():
    """Growth is one-way; the re-seat must be too.

    Clearing a tall label after finalize must not raise the source back up
    out of the reserved band (the axes cannot shrink back down).
    """
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall",
        source=SOURCE,
    )
    x_axis_label(ax, "Sweep budget\nsamples per monitor")
    seated = _source_bbox(fig)
    x_axis_label(ax, "")
    after_clear = _source_bbox(fig)
    assert abs(after_clear.y0 - seated.y0) < 1e-6, (
        f"clearing the label re-raised the source: {seated.y0:.4f} -> "
        f"{after_clear.y0:.4f}"
    )
    plt.close(fig)
