"""``x_axis_label(unit=…)`` — the muted unit line below the x-axis label.

The unit is an annotation anchored to the label artist, mirroring
``y_axis_label``'s stacked "metric / unit" convention. It must sit below
the label in the muted colour, keep clear of the source line in both call
orders (the bottom band reserves its height), be replaced rather than
stacked on a re-call, and ride through a deck-variant save.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.transforms import Bbox

from graphs import C_LABEL_MUTED, finalize, save_deck_variant, set_theme, x_axis_label

SOURCE = "Source: Touchstone rollouts"
XLABEL = "Rate per in-the-wild conversation"
UNIT = "% (log scale)"


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


def _source_bbox(fig):
    artists = [t for t in fig.texts if SOURCE.split()[0] in t.get_text()]
    assert artists, "source line was not rendered"
    return Bbox.union([_fig_bbox(fig, t) for t in artists])


def _unit_artist(ax):
    unit = getattr(ax, "_graphs_xlabel_unit", None)
    assert unit is not None, "unit annotation was not created"
    return unit


def _labelled_chart(*, label_when: str):
    """A line chart with a source line; the unit label set before or after finalize."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    if label_when == "before":
        x_axis_label(ax, XLABEL, unit=UNIT)
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall\n% of attack transcripts flagged",
        source=SOURCE,
    )
    if label_when == "after":
        x_axis_label(ax, XLABEL, unit=UNIT)
    return fig, ax


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_unit_sits_below_the_label_in_the_muted_colour(label_when):
    fig, ax = _labelled_chart(label_when=label_when)
    unit = _unit_artist(ax)
    assert unit.get_color() == C_LABEL_MUTED
    label_bb = _fig_bbox(fig, ax.xaxis.label)
    unit_bb = _fig_bbox(fig, unit)
    assert unit_bb.y1 <= label_bb.y0 + 1e-6, "unit line must hang below the label"
    label_mid = (label_bb.x0 + label_bb.x1) / 2
    unit_mid = (unit_bb.x0 + unit_bb.x1) / 2
    assert abs(unit_mid - label_mid) < 0.01, "unit line must centre under the label"


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_unit_and_source_do_not_overlap(label_when):
    """The bottom band must reserve the unit line's height in both call orders."""
    fig, ax = _labelled_chart(label_when=label_when)
    unit_bb = _fig_bbox(fig, _unit_artist(ax))
    source_bb = _source_bbox(fig)
    assert unit_bb.y0 >= source_bb.y1 - 1e-6, "unit line paints over the source"
    assert source_bb.y0 >= 0.0, "source line pushed off-canvas"


def test_recall_replaces_the_unit_rather_than_stacking():
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    x_axis_label(ax, XLABEL, unit="%")
    first = ax._graphs_xlabel_unit
    x_axis_label(ax, XLABEL, unit=UNIT)
    assert ax._graphs_xlabel_unit is not first
    unit_texts = [t.get_text() for t in ax.texts if t.get_text() in ("%", UNIT)]
    assert unit_texts == [UNIT]


def test_relabelling_without_a_unit_clears_the_previous_one():
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    x_axis_label(ax, XLABEL, unit="%")
    x_axis_label(ax, XLABEL)
    assert getattr(ax, "_graphs_xlabel_unit", None) is None
    assert not [t for t in ax.texts if t.get_text() == "%"]


def test_unit_and_footnote_rows_do_not_overlap():
    """``footnotes()`` must drop its rows below the unit line, not just the label."""
    from graphs import footnotes

    fig, ax = plt.subplots(figsize=(7.0, 5.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    ax.set_xticks([0, 1, 2, 3])  # pin ticks inside the data range: no phantom edge labels
    x_axis_label(ax, XLABEL, unit=UNIT)
    finalize(ax, title="Recall rises with sweep budget", footnote_lines=2)
    footnotes(
        fig,
        "first note: a definition long enough to need its own row in the stack.",
        "second note: another definition row beneath the first.",
        source=SOURCE,
    )
    unit_bb = _fig_bbox(fig, _unit_artist(ax))
    rows = [
        t
        for t in fig.texts
        if "note" in t.get_text() or SOURCE.split()[0] in t.get_text()
    ]
    assert rows, "footnote rows were not rendered"
    highest_row_top = max(_fig_bbox(fig, t).y1 for t in rows)
    assert highest_row_top <= unit_bb.y0 + 1e-6, "footnote rows paint over the unit line"


def test_deck_variant_save_carries_the_unit(tmp_path):
    """The unit is an axes-level artist, so the deck strip must leave it alone."""
    fig, ax = _labelled_chart(label_when="before")
    full = tmp_path / "chart.png"
    fig.savefig(full, bbox_inches="tight")
    deck_path = save_deck_variant(fig, full)
    assert deck_path.exists()
    # Whether the strip ran on a pickled clone or in place, the live axes
    # must still carry exactly one unit annotation with the unit text.
    assert [t.get_text() for t in ax.texts if t.get_text() == UNIT] == [UNIT]
