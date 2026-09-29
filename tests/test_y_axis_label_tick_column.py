"""y_axis_label heads the tick column: flush with its outer edge, above its top label.

The block used to anchor to the axes spine, leaving it a gutter's width left of
the "100%" it is meant to title (the touchstone precision-ladder deck figure).
A top legend that clears the block horizontally now shares its strip instead
of stacking a second band under the descriptor.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter

from graphs import finalize, set_theme, top_legend, y_axis_label

TITLE = "Which prompting strategy buys the most precision at 95% recall?"
DESCRIPTOR = "Recall measured against the jury's labels for the watched harm"
LABEL = "precision at 95% recall"
UNIT = "% of fires that are the watched harm"
NOTES = (
    (
        "Colour is what the lever does, not how well it does it, spelled out at length "
        "so that this note wraps onto a second row of the footnote band."
    ),
    (
        "Claude Opus 4.8 and Claude Opus 5 averaged, each at its own 95%-recall "
        "threshold; rungs are each lever family's best deployable arm."
    ),
    "Added after the pool's rows were published, so it reads on its own scored rows.",
)
SOURCE = "Source: ShareTrawl bycatch pool (N=3,608); precision_ladder.py"
PT = 1.0 / 72.0


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _bar_fig(*, ceiling: float = 1.05):
    fig, ax = plt.subplots(figsize=(7.0, 5.0))
    ax.bar(range(6), [0.55, 0.78, 0.79, 0.86, 0.94, 0.95], width=0.68)
    ax.set_xticks(range(6))
    ax.set_xticklabels([f"rung {i}" for i in range(6)], fontsize=8)
    ax.set_ylim(0, ceiling)
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    ax.grid(axis="y", alpha=0.5)
    ax.grid(axis="x", visible=False)
    return fig, ax


def _fig_bboxes(fig, artists):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return [a.get_window_extent(renderer=renderer).transformed(inv) for a in artists]


def _label_bboxes(fig):
    return _fig_bboxes(fig, [t for t in fig.texts if t.get_text() in (LABEL, UNIT)])


def _tick_column_bboxes(fig, ax):
    frozen = [t for t in ax.texts if t.get_gid() == "y-labels-on-grid"]
    labels = frozen or [
        t for t in ax.get_yticklabels() if t.get_visible() and t.get_text()
    ]
    return _fig_bboxes(fig, labels)


def test_right_label_edge_meets_tick_column_edge():
    """The block's right edge lands on the tick labels' outer edge, not the spine."""
    fig, ax = _bar_fig()
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)

    label_x1 = max(bb.x1 for bb in _label_bboxes(fig))
    column_x1 = max(bb.x1 for bb in _tick_column_bboxes(fig, ax))
    axes_x1 = ax.get_position().x1
    assert column_x1 > axes_x1 + 2 * PT / 7.0, (
        "tick column should sit right of the spine"
    )
    assert label_x1 == pytest.approx(column_x1, abs=PT / 7.0), (
        f"label x1 {label_x1:.4f} should meet the tick column x1 {column_x1:.4f}"
    )


def test_left_label_edge_meets_left_tick_column_edge():
    """Mirror image on a left-hand axis: the block's left edge meets the column's."""
    fig, ax = _bar_fig()
    y_axis_label(ax, LABEL, unit=UNIT, side="left")
    finalize(
        ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False, y_axis_right=False
    )

    label_x0 = min(bb.x0 for bb in _label_bboxes(fig))
    column_x0 = min(bb.x0 for bb in _tick_column_bboxes(fig, ax))
    assert label_x0 == pytest.approx(column_x0, abs=PT / 7.0), (
        f"label x0 {label_x0:.4f} should meet the tick column x0 {column_x0:.4f}"
    )


def test_label_clears_a_ceiling_tick_label():
    """With a 100% tick at the axes ceiling, its on-grid label pokes above the axes
    top into the block's footprint; the block must seat above it, not on it."""
    fig, ax = _bar_fig(ceiling=1.0)
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)

    column = _tick_column_bboxes(fig, ax)
    top_tick = max(column, key=lambda bb: bb.y1)
    assert top_tick.y1 > ax.get_position().y1, "the ceiling tick should overshoot"
    label_bottom = min(bb.y0 for bb in _label_bboxes(fig))
    assert label_bottom >= top_tick.y1 - 1e-4, (
        f"label bottom {label_bottom:.4f} sits on the ceiling tick label (top {top_tick.y1:.4f})"
    )


def test_label_after_finalize_still_meets_tick_column():
    """The manual path anchors to the frozen column too — it is final by then."""
    fig, ax = _bar_fig()
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)
    y_axis_label(ax, LABEL, unit=UNIT)

    label_x1 = max(bb.x1 for bb in _label_bboxes(fig))
    column_x1 = max(bb.x1 for bb in _tick_column_bboxes(fig, ax))
    assert label_x1 == pytest.approx(column_x1, abs=PT / 7.0)


def _legend_fig(labels, **legend_kwargs):
    fig, ax = _bar_fig()
    handles = [Patch(facecolor="C0") for _ in labels]
    top_legend(fig, handles, labels, **legend_kwargs)
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, zero_rule=False)
    return fig, ax


def test_short_legend_shares_the_label_strip():
    """A legend that clears the block horizontally sits level with it, and the
    descriptor closes up: no blank legend-height band above the row."""
    fig, ax = _legend_fig(["no lever", "label competition"])
    legend_bb = _fig_bboxes(fig, [fig.legends[0]])[0]
    label = _label_bboxes(fig)
    label_top = max(bb.y1 for bb in label)
    label_bottom = min(bb.y0 for bb in label)
    assert legend_bb.x1 < min(bb.x0 for bb in label), (
        "precondition: legend clears the block"
    )
    assert legend_bb.y0 < label_top, (
        f"legend bottom {legend_bb.y0:.4f} stacked above the label top {label_top:.4f}"
    )
    assert legend_bb.y0 >= label_bottom - 1e-3, "legend dropped below the block's seat"

    descriptor = next(t for t in fig.texts if t.get_text().startswith("Recall"))
    desc_bb = _fig_bboxes(fig, [descriptor])[0]
    strip_top = max(label_top, legend_bb.y1)
    assert desc_bb.y0 >= strip_top, "descriptor overlaps the shared strip"
    assert desc_bb.y0 - strip_top < 12 * PT / 5.0, (
        f"descriptor floats {(desc_bb.y0 - strip_top) / (PT / 5.0):.1f}pt above the strip"
    )


def test_wide_legend_still_stacks_above_the_label():
    """A legend that runs under the block keeps its own band above it."""
    entries = [f"a long legend entry number {i}" for i in range(6)]
    fig, ax = _legend_fig(entries, ncol=6)
    legend_bb = _fig_bboxes(fig, [fig.legends[0]])[0]
    label = _label_bboxes(fig)
    assert legend_bb.x1 > min(bb.x0 for bb in label), (
        "precondition: legend reaches the block"
    )
    assert legend_bb.y0 >= max(bb.y1 for bb in label) - 1e-4, (
        "overlapping legend must stack"
    )
    assert not any(legend_bb.overlaps(bb) for bb in label)


def test_shared_strip_legend_clears_the_panel_label_band():
    """Sharing the strip with a left-hand block, a legend placed clear of it on
    the right must still seat above the top-row ``panel_label`` band — the
    heading's rule spans the row, not just the label's side."""
    from graphs._finalize import AUTO_LAYOUT_PANEL_LABEL_PT

    fig, ax = _bar_fig()
    handles = [Patch(facecolor="C0") for _ in range(2)]
    top_legend(fig, handles, ["no lever", "label competition"], x=0.55)
    y_axis_label(ax, LABEL, unit=UNIT, side="left")
    finalize(
        ax,
        title=TITLE,
        descriptor=DESCRIPTOR,
        zero_rule=False,
        y_axis_right=False,
        panel_labels=True,
    )

    legend_bb = _fig_bboxes(fig, [fig.legends[0]])[0]
    label = _label_bboxes(fig)
    assert legend_bb.x0 > max(bb.x1 for bb in label), (
        "precondition: legend clears the block"
    )
    panel_band = AUTO_LAYOUT_PANEL_LABEL_PT * PT / 5.0
    assert legend_bb.y0 >= ax.get_position().y1 + panel_band - 1e-4, (
        f"legend bottom {legend_bb.y0:.4f} sits inside the panel_label band"
    )
    descriptor = next(t for t in fig.texts if t.get_text().startswith("Recall"))
    desc_bb = _fig_bboxes(fig, [descriptor])[0]
    assert desc_bb.y0 >= legend_bb.y1, "descriptor overlaps the legend"


@pytest.mark.parametrize("ceiling", [1.05, 1.0])
def test_footnotes_after_finalize_keeps_the_block_clear(ceiling):
    """``footnotes`` grows the bottom band afterwards by raising the panel bottoms,
    compressing the data range: the top tick's label climbs toward the axes top
    and the legend's axes-fraction anchor slides. The block must stay above the
    column with air, below the descriptor, and level with the legend."""
    from graphs import footnotes
    from graphs._finalize import COLUMN_TOP_CLEARANCE_PT

    fig, ax = _bar_fig(ceiling=ceiling)
    handles = [Patch(facecolor="C0") for _ in range(2)]
    top_legend(fig, handles, ["no lever", "label competition"])
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, source="", zero_rule=False)
    seated_bottom = min(bb.y0 for bb in _label_bboxes(fig))
    footnotes(fig, *NOTES, source=SOURCE)

    column_top = max(bb.y1 for bb in _tick_column_bboxes(fig, ax))
    label = _label_bboxes(fig)
    label_bottom = min(bb.y0 for bb in label)
    label_top = max(bb.y1 for bb in label)
    air = COLUMN_TOP_CLEARANCE_PT * PT / 5.0
    assert label_bottom >= column_top + air - 1e-4, (
        f"label bottom {label_bottom:.4f} sits on the tick column (top {column_top:.4f})"
    )
    assert label_bottom == pytest.approx(seated_bottom, abs=1e-4), (
        f"block bottom moved {seated_bottom:.4f} -> {label_bottom:.4f}: the column "
        "was not held, so the block lifted off its seat"
    )
    descriptor = next(t for t in fig.texts if t.get_text().startswith("Recall"))
    desc_bb = _fig_bboxes(fig, [descriptor])[0]
    assert desc_bb.y0 >= label_top - 1e-4, "label pushed into the descriptor"
    # The legend seats on the axes top (a ceiling tick lifts the block alone, so
    # the two need not be level); it must not have slid below that seat.
    from graphs._finalize import Y_AXIS_LABEL_MARGIN

    legend_bb = _fig_bboxes(fig, [fig.legends[0]])[0]
    seat = ax.get_position().y1 + Y_AXIS_LABEL_MARGIN
    assert legend_bb.y0 >= seat - 1e-3, (
        f"legend bottom {legend_bb.y0:.4f} slid below its seat {seat:.4f}"
    )
    assert legend_bb.y0 < label_top, "legend no longer shares the strip"


def test_footnotes_leaves_the_axes_top_alone_when_the_column_has_air():
    """A column whose top label sits well under the axes top can climb into that
    air without lifting the block, so the hold must not shorten the panel."""
    from graphs import footnotes

    fig, ax = _bar_fig(ceiling=1.19)  # top tick 100% at 84% of the axes height
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, source="", zero_rule=False)
    axes_top = ax.get_position().y1
    seated_bottom = min(bb.y0 for bb in _label_bboxes(fig))
    column_top = max(bb.y1 for bb in _tick_column_bboxes(fig, ax))
    assert column_top < axes_top - 0.02, "fixture must leave air above the column"
    footnotes(fig, *NOTES, source=SOURCE)

    assert ax.get_position().y1 == pytest.approx(axes_top, abs=1e-6), (
        "the panel top was lowered although the column had air under the block"
    )
    label_bottom = min(bb.y0 for bb in _label_bboxes(fig))
    assert label_bottom == pytest.approx(seated_bottom, abs=1e-4)


def test_footnotes_hold_keeps_facet_tops_level():
    """On a faceted row the hold lowers every panel by the same amount: the
    labelled panel's top must not drop below its unlabelled siblings'."""
    from graphs import footnotes

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 4.5), sharey=True)
    for ax in axes:
        ax.bar(range(4), [0.55, 0.78, 0.86, 0.95], width=0.68)
        ax.set_ylim(0, 1.05)  # the 100% label sits just under the axes top
    axes[0].yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    y_axis_label(axes[0], LABEL, unit=UNIT)
    finalize(axes[0], title=TITLE, descriptor=DESCRIPTOR, source="", zero_rule=False)
    tops_before = [ax.get_position().y1 for ax in axes]
    assert tops_before[0] == pytest.approx(tops_before[1], abs=1e-9)
    footnotes(fig, *NOTES, source=SOURCE)

    tops_after = [ax.get_position().y1 for ax in axes]
    assert tops_after[0] < tops_before[0] - 1e-4, "fixture must engage the hold"
    assert tops_after[0] == pytest.approx(tops_after[1], abs=1e-9), (
        f"facet tops diverged after footnotes: {tops_after[0]:.4f} vs {tops_after[1]:.4f}"
    )
