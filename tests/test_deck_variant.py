"""save_deck_variant: strip headline furniture, keep the chart."""

import matplotlib

matplotlib.use("Agg")

import pickle

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import FuncFormatter
from PIL import Image

from graphs import (
    finalize,
    footnotes,
    panel_label,
    save_deck_variant,
    set_theme,
    subplots,
    y_axis_label,
)
from graphs._deck import _has_y_axis_labelling

TITLE = "Bold headline claim"
DESCRIPTOR = "Metric* and unit"
SOURCE = "Source: somewhere (N=12); test_deck_variant.py"
NOTE = "*Metric: a coined term defined here"
Y_LABEL = "flag rate"
Y_UNIT = "% of probes fired"
PANEL = "Panel heading"


def _chart(*, formatter=None):
    set_theme()
    fig, ax = subplots("daily", height=3.4)
    ax.plot(np.arange(6), np.arange(6) * 1.5, label="series")
    if formatter is not None:
        ax.yaxis.set_major_formatter(formatter)
    y_axis_label(ax, Y_LABEL, unit=Y_UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, source="", panel_labels=True)
    panel_label(ax, PANEL)
    footnotes(fig, NOTE, source=SOURCE, verify=False)
    return fig, ax


def _texts(fig) -> set[str]:
    return {t.get_text() for t in fig.texts if t.get_text()}


def test_deck_variant_strips_headline_keeps_chart(tmp_path):
    fig, _ = _chart()
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    deck = save_deck_variant(fig, full)

    assert deck == tmp_path / "chart_deck.png"
    assert deck.is_file()
    # The live figure is untouched (pickle-clone path): headline still there.
    joined = " ".join(_texts(fig))
    assert TITLE in joined
    assert "Source: somewhere" in joined
    # The deck render is shorter than the full chart (title + footnote band gone).
    with Image.open(full) as im_full, Image.open(deck) as im_deck:
        assert im_deck.height < im_full.height
        assert im_deck.width == pytest.approx(im_full.width, abs=6)


def test_tagging_separates_headline_from_kept_artists():
    fig, _ = _chart()
    kept, stripped = [], []
    for t in fig.texts:
        (stripped if getattr(t, "_graphs_deck_strip", False) else kept).append(t.get_text())
    kept_joined = " ".join(kept)
    stripped_joined = " ".join(stripped)
    # y_axis_label block and panel_label survive; headline text does not.
    assert Y_LABEL in kept_joined
    assert Y_UNIT in kept_joined
    assert PANEL in kept_joined
    assert TITLE in stripped_joined
    assert "coined term" in stripped_joined
    assert "Source: somewhere" in stripped_joined
    assert TITLE not in kept_joined
    assert "Source: somewhere" not in kept_joined


def test_unpicklable_figure_falls_back_to_in_place(tmp_path):
    fig, _ = _chart(formatter=FuncFormatter(lambda v, _: f"{v:.0f}%"))
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    deck = save_deck_variant(fig, full)

    assert deck.is_file()
    # In-place fallback: the live figure lost its headline.
    assert TITLE not in " ".join(_texts(fig))


def test_empty_note_with_source_still_tagged_for_strip():
    """``footnotes(fig, "", source=..., y=...)`` — an empty note plus an explicit source and y.

    Regression: the source-aware branch's ``if not notes_clean: return`` used to return before
    ``_mark_deck_strip``, so a source line rendered with no notes (a bare source string, common
    when the caller has no footnote to add) survived into the deck variant untagged.
    """
    set_theme()
    fig, ax = subplots("daily", height=3.4)
    ax.plot(np.arange(6), np.arange(6) * 1.5)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, source="")
    footnotes(fig, "", source=SOURCE, y=0.04, verify=False)
    stripped = [t.get_text() for t in fig.texts if getattr(t, "_graphs_deck_strip", False)]
    assert "Source: somewhere" in " ".join(stripped)


def test_warns_when_nothing_to_strip(tmp_path):
    set_theme()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with pytest.warns(UserWarning, match="no headline artists"):
        save_deck_variant(fig, tmp_path / "bare.png")


def _descriptor_only_chart(*, ylabel: str | None = None, picklable: bool = False):
    """A chart whose ONLY y-axis labelling is the descriptor (no y_axis_label block).

    By default the ``FuncFormatter`` lambda makes the figure unpicklable,
    forcing the in-place strip path so tests can inspect the live figure as
    the deck state; ``picklable=True`` skips the formatter so the figure
    takes ``save_deck_variant``'s default pickle-clone path.
    """
    set_theme()
    fig, ax = subplots("daily", height=3.4)
    ax.plot(np.arange(6), np.arange(6) * 1.5)
    if not picklable:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}%"))
    if ylabel is not None:
        ax.set_ylabel(ylabel)
    finalize(
        ax,
        title=TITLE,
        descriptor=DESCRIPTOR,
        source="",
        allow_ylabel=ylabel is not None,
    )
    footnotes(fig, NOTE, source=SOURCE, verify=False)
    return fig, ax


def test_descriptor_kept_when_it_is_the_only_y_axis_labelling(tmp_path):
    """No y_axis_label block, no ylabel — the descriptor IS the y-axis label, so it stays."""
    fig, _ = _descriptor_only_chart()
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    deck = save_deck_variant(fig, full)

    assert deck.is_file()
    joined = " ".join(_texts(fig))  # in-place strip: the live figure is the deck state
    assert "Metric" in joined  # descriptor survives
    assert TITLE not in joined
    assert "Source: somewhere" not in joined
    assert "coined term" not in joined  # footnotes still stripped


def test_descriptor_stripped_when_y_axis_label_block_present(tmp_path):
    """A y_axis_label block already labels the axis — the descriptor strips as before."""
    fig, _ = _chart(formatter=FuncFormatter(lambda v, _: f"{v:.0f}%"))
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    save_deck_variant(fig, full)

    joined = " ".join(_texts(fig))
    assert Y_LABEL in joined  # the block survives
    assert "Metric" not in joined  # the descriptor does not
    assert TITLE not in joined


def test_descriptor_stripped_when_axes_ylabel_allowed(tmp_path):
    """An allow_ylabel axes label (coordinate plot / twinx) counts as y-axis labelling."""
    fig, ax = _descriptor_only_chart(ylabel="true-positive rate")
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    save_deck_variant(fig, full)

    joined = " ".join(_texts(fig))
    assert "Metric" not in joined
    assert ax.get_ylabel() == "true-positive rate"


def test_descriptor_decision_survives_pickle_clone(tmp_path):
    """The default clone path: the keep/strip decision's inputs survive pickle.

    ``save_deck_variant`` decides ``keep_descriptor`` on a pickled clone, so it
    depends on two custom attributes surviving the round-trip — the
    ``_graphs_deck_descriptor`` tag on the descriptor's artists and
    ``fig._graphs_y_axis_labels`` behind ``_has_y_axis_labelling``. Matplotlib's
    ``__getstate__`` happens to preserve both today; pin that, in both
    directions of the decision, so a pickling change can't silently flip deck
    variants while the in-place-path tests stay green.
    """
    fig, _ = _descriptor_only_chart(picklable=True)
    full = tmp_path / "chart.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")

    deck = save_deck_variant(fig, full)

    assert deck.is_file()
    assert TITLE in " ".join(_texts(fig))  # live figure untouched: the clone path ran
    clone = pickle.loads(pickle.dumps(fig))
    assert not _has_y_axis_labelling(clone)  # descriptor-only chart: keep
    assert any(getattr(t, "_graphs_deck_descriptor", False) for t in clone.texts)

    fig_block, _ = _chart()  # y_axis_label block: the clone must still say strip
    clone_block = pickle.loads(pickle.dumps(fig_block))
    assert _has_y_axis_labelling(clone_block)


def test_descriptor_artists_carry_both_deck_tags():
    fig, _ = _chart()
    descriptor_artists = [
        t for t in fig.texts if getattr(t, "_graphs_deck_descriptor", False)
    ]
    assert descriptor_artists
    assert all(getattr(t, "_graphs_deck_strip", False) for t in descriptor_artists)
    joined = " ".join(t.get_text() for t in descriptor_artists)
    assert "Metric" in joined
    assert TITLE not in joined
