"""y_axis_label on two-row grids, with a wrapped label, and before the axis flips.

Three gaps found by the touchstone figure sweep (PR #4618): a lower row's block
overprinted the row above because ``hspace`` never budgeted it; a label that
wrapped to two lines dropped its unit line into the axes; and the band reserved
before ``finalize`` flipped the y-axis right ignored the tick column's overshoot,
so the block met the descriptor once the column was frozen.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.ticker import PercentFormatter

from graphs import finalize, panel_label, set_theme, y_axis_label
from graphs._finalize import AUTO_LAYOUT_HSPACE_GUTTER_PT

PT = 1.0 / 72.0
TITLE = "Does one global cut hold across context lengths?"
DESCRIPTOR = "One CRC cut on the pooled negatives vs a same-budget cut per length band"


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _bboxes(fig, artists):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return [a.get_window_extent(renderer=renderer).transformed(inv) for a in artists]


def _texts(fig, *needles):
    return [t for t in fig.texts if any(t.get_text().startswith(n) for n in needles)]


def test_lower_row_label_gets_its_own_room_in_the_row_gap():
    """A y_axis_label on the second row must not overprint the first row's axes
    or its x-tick labels — the inter-row gap has to grow for it. Independent x
    axes, so the upper row keeps its tick labels and the check is live."""
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(7.0, 6.0))
    xs = [30e3, 60e3, 120e3, 240e3, 480e3, 800e3]
    top.plot(xs, [0.95, 0.95, 0.9, 0.85, 0.7, 0.45], marker="o")
    top.set_ylim(0, 1.03)
    bottom.plot(xs, [97, 97, 96, 95, 90, 35], marker="o")
    bottom.set_ylim(0, 100)
    for ax in (top, bottom):
        ax.set_xscale("log")
        ax.grid(axis="y", alpha=0.5)
    y_axis_label(top, "recall on matched positives", unit="0–1")
    y_axis_label(bottom, "monitor score", unit="0–100, medians and the two cuts")
    finalize(top, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)

    lower = _bboxes(fig, _texts(fig, "monitor score", "0–100"))
    lower_top = max(bb.y1 for bb in lower)
    top_axes_bottom = top.get_position().y0
    assert lower_top <= top_axes_bottom + 1e-4, (
        f"lower row's label (top {lower_top:.4f}) overprints the upper axes "
        f"(bottom {top_axes_bottom:.4f})"
    )
    upper_ticks = [t for t in top.get_xticklabels() if t.get_visible() and t.get_text()]
    assert upper_ticks, "precondition: the upper row shows x-tick labels"
    # The gap is budgeted against the *final* axes height: the ticks clear the
    # block by the full gutter, not a fraction of it.
    gutter = AUTO_LAYOUT_HSPACE_GUTTER_PT * PT / 6.0
    for bb in _bboxes(fig, upper_ticks):
        assert bb.y0 >= lower_top + gutter - 1e-4, (
            f"upper x-tick (bottom {bb.y0:.4f}) sits within the gutter of the lower "
            f"label (top {lower_top:.4f})"
        )
    bottom_axes_top = bottom.get_position().y1
    assert min(bb.y0 for bb in lower) >= bottom_axes_top - 1e-4, (
        "label dipped into its axes"
    )


def test_lower_row_label_with_panel_labels_clears_both_bands():
    """With ``panel_labels=True`` the lower row's left-side block lifts over the
    panel_label band as well; the gap must hold both."""
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(7.0, 6.0), sharex=True)
    top.plot([1, 2, 3], [0.2, 0.5, 0.9])
    bottom.plot([1, 2, 3], [20, 50, 90])
    for ax in (top, bottom):
        ax.grid(axis="y", alpha=0.5)
    y_axis_label(bottom, "monitor score", unit="0–100", side="left")
    finalize(
        top,
        title=TITLE,
        descriptor=DESCRIPTOR,
        zero_rule=False,
        y_axis_right=False,
        panel_labels=True,
    )
    panel_label(top, "Recall")
    panel_label(bottom, "Score")

    lower = _bboxes(fig, _texts(fig, "monitor score", "0–100"))
    assert max(bb.y1 for bb in lower) <= top.get_position().y0 + 1e-4
    # ``panel_label`` draws its heading as figure text on the same left anchor;
    # the block must sit above it.
    heading = _bboxes(fig, [t for t in fig.texts if t.get_text() == "Score"])
    assert heading, "precondition: the panel heading rendered"
    assert min(bb.y0 for bb in lower) >= heading[0].y1 - 1e-4, (
        "label block overlaps the panel heading"
    )


def test_lower_row_only_label_leaves_the_top_margin_alone():
    """A block on the second row alone seats in the inter-row gap; it must not
    also push the title stack up as if it headed the top row."""

    def descriptor_gap(with_label: bool) -> float:
        fig, (top, bottom) = plt.subplots(2, 1, figsize=(7.0, 6.0), sharex=True)
        top.plot([1, 2, 3], [0.2, 0.5, 0.9])
        bottom.plot([1, 2, 3], [20, 50, 90])
        if with_label:
            y_axis_label(bottom, "monitor score", unit="0–100")
        finalize(top, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)
        desc = _bboxes(fig, _texts(fig, "One CRC"))[0]
        gap = desc.y0 - top.get_position().y1
        plt.close(fig)
        return gap

    assert abs(descriptor_gap(True) - descriptor_gap(False)) <= 1e-3, (
        "a lower-row label grew the top margin"
    )


def test_wrapped_label_keeps_its_unit_line_out_of_the_axes():
    """A label that wraps to two lines used to drop the unit a whole line below
    the seat — into the plot. The unit sits directly under the text block."""
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    ax.bar(range(4), [0.3, 0.5, 0.7, 0.9])
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", alpha=0.5)
    long_label = "share of absent-behaviour judgements that fire on the sibling probe"
    y_axis_label(ax, long_label, unit="% of judgements", width_frac=0.35)
    finalize(ax, title="Short", descriptor="", zero_rule=False)

    text = [t for t in fig.texts if t.get_text().startswith("share of")]
    assert text and "\n" in text[0].get_text(), "precondition: the label wraps"
    text_bb = _bboxes(fig, text)[0]
    unit_bb = _bboxes(fig, _texts(fig, "% of judgements"))[0]
    assert unit_bb.y0 >= ax.get_position().y1 - 1e-4, (
        f"unit line (bottom {unit_bb.y0:.4f}) sits inside the axes (top {ax.get_position().y1:.4f})"
    )
    assert unit_bb.y1 <= text_bb.y0 + 2 * PT / 4.0, (
        "unit line is not directly under the text"
    )


def test_band_reserves_the_column_overshoot_before_the_axis_flips():
    """Before ``finalize`` the native tick labels still sit on the left while the
    block is mounted right; the band must still budget the ceiling tick's
    overshoot, or the block meets the descriptor once the column is frozen."""
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.bar(range(6), [0.55, 0.78, 0.79, 0.86, 0.94, 0.95], width=0.68)
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", alpha=0.5)
    assert ax.yaxis.get_ticks_position() in ("left", "default"), (
        "precondition: ticks left"
    )
    y_axis_label(
        ax, "precision at 95% recall", unit="% of fires that are the watched harm"
    )
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)

    label = _bboxes(fig, _texts(fig, "precision at", "% of fires"))
    desc = _bboxes(fig, _texts(fig, "One CRC"))[0]
    gap = desc.y0 - max(bb.y1 for bb in label)
    assert gap >= 3 * PT / 5.0 - 1e-4, (
        f"label top is {gap / (PT / 5.0):.1f}pt from the descriptor; the band did not "
        "reserve the column's overshoot"
    )
