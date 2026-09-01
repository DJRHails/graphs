"""``x_axis_label(unit=…)`` — the muted unit joined to (or stacked under) the label.

Mirrors ``y_axis_label``'s "metric / unit" convention on the x axis. When the
one-line ``"text, unit"`` composite fits the axes width the unit renders inline
as a muted ``", unit"`` continuation (two chunks over an ``alpha=0`` native
label); a composite too wide for the axes stacks the unit on a second line
below. Both modes must keep clear of the source/footnote band, be replaced
rather than stacked on a re-call, and ride through a deck-variant save.
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
# Long enough that "text, unit" cannot fit the axes on the test figures below.
XLABEL_WIDE = (
    "Rate per in-the-wild conversation, measured over the whole fresh corpus "
    "head with re-shares collapsed at the source"
)


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


def _labelled_chart(*, label_when: str, text: str = XLABEL):
    """A line chart with a source line; the unit label set before or after finalize."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    ax.set_xticks([0, 1, 2, 3])  # pin ticks inside the data range: no phantom edge labels
    if label_when == "before":
        x_axis_label(ax, text, unit=UNIT)
    finalize(
        ax,
        title="Recall rises with sweep budget",
        descriptor="Monitor recall\n% of attack transcripts flagged",
        source=SOURCE,
    )
    if label_when == "after":
        x_axis_label(ax, text, unit=UNIT)
    return fig, ax


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_fitting_unit_joins_the_label_line_in_the_muted_colour(label_when):
    fig, ax = _labelled_chart(label_when=label_when)
    assert ax._graphs_xlabel_inline
    unit = _unit_artist(ax)
    assert unit.get_text() == f", {UNIT}"
    assert unit.get_color() == C_LABEL_MUTED
    assert ax.xaxis.label.get_text() == f"{XLABEL}, {UNIT}"
    assert ax.xaxis.label.get_alpha() == 0.0
    label_bb = _fig_bbox(fig, ax.xaxis.label)
    unit_bb = _fig_bbox(fig, unit)
    assert abs(unit_bb.y0 - label_bb.y0) < 1e-6, "inline unit must share the label's line"
    assert abs(unit_bb.x1 - label_bb.x1) < 1e-6, "inline unit must end the composite"


@pytest.mark.parametrize("label_when", ["before", "after"])
def test_overwide_composite_stacks_the_unit_below_the_label(label_when):
    fig, ax = _labelled_chart(label_when=label_when, text=XLABEL_WIDE)
    assert not ax._graphs_xlabel_inline
    unit = _unit_artist(ax)
    assert unit.get_text() == UNIT
    assert unit.get_color() == C_LABEL_MUTED
    label_bb = _fig_bbox(fig, ax.xaxis.label)
    unit_bb = _fig_bbox(fig, unit)
    assert unit_bb.y1 <= label_bb.y0 + 1e-6, "stacked unit must hang below the label"


@pytest.mark.parametrize("text", [XLABEL, XLABEL_WIDE])
@pytest.mark.parametrize("label_when", ["before", "after"])
def test_unit_and_source_do_not_overlap(label_when, text):
    """The bottom band must clear the unit in both modes and call orders."""
    fig, ax = _labelled_chart(label_when=label_when, text=text)
    unit_bb = _fig_bbox(fig, _unit_artist(ax))
    source_bb = _source_bbox(fig)
    assert unit_bb.y0 >= source_bb.y1 - 1e-6, "unit paints over the source"
    assert source_bb.y0 >= 0.0, "source line pushed off-canvas"


def test_recall_replaces_the_unit_and_restores_the_label():
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    x_axis_label(ax, XLABEL, unit="%")  # inline: label hidden under two chunks
    assert ax._graphs_xlabel_inline and len(ax._graphs_xlabel_chunks) == 2
    x_axis_label(ax, XLABEL_WIDE, unit=UNIT)  # re-call flips to stacked
    assert not ax._graphs_xlabel_inline and len(ax._graphs_xlabel_chunks) == 1
    assert ax.xaxis.label.get_alpha() is None, "re-call must restore the label's alpha"
    leftovers = [t.get_text() for t in ax.texts if t.get_text() in (XLABEL, ", %", "%")]
    assert leftovers == [], f"stale unit chunks left behind: {leftovers}"


def test_relabelling_without_a_unit_clears_the_previous_one():
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    x_axis_label(ax, XLABEL, unit="%")
    x_axis_label(ax, XLABEL)
    assert getattr(ax, "_graphs_xlabel_unit", None) is None
    assert ax.xaxis.label.get_alpha() is None
    assert ax.xaxis.label.get_text() == XLABEL
    assert not [t for t in ax.texts if t.get_text() in ("%", ", %")]


def test_unit_and_footnote_rows_do_not_overlap():
    """``footnotes()`` must drop its rows below a stacked unit, not just the label."""
    from graphs import footnotes

    fig, ax = plt.subplots(figsize=(7.0, 5.4))
    ax.plot([0, 1, 2, 3], [10, 30, 25, 40])
    ax.set_xticks([0, 1, 2, 3])  # pin ticks inside the data range: no phantom edge labels
    x_axis_label(ax, XLABEL_WIDE, unit=UNIT)
    assert not ax._graphs_xlabel_inline
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


@pytest.mark.parametrize("text", [XLABEL, XLABEL_WIDE])
def test_deck_variant_save_carries_the_unit(tmp_path, text):
    """The unit artists are axes-level, so the deck strip must leave them alone."""
    fig, ax = _labelled_chart(label_when="before", text=text)
    full = tmp_path / "chart.png"
    fig.savefig(full, bbox_inches="tight")
    deck_path = save_deck_variant(fig, full)
    assert deck_path.exists()
    # Whether the strip ran on a pickled clone or in place, the live axes must
    # still carry exactly one muted unit annotation.
    unit_text = _unit_artist(ax).get_text()
    assert [t.get_text() for t in ax.texts if t.get_text() == unit_text] == [unit_text]
