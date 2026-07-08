"""save_deck_variant: strip headline furniture, keep the chart."""

import matplotlib

matplotlib.use("Agg")

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


def test_warns_when_nothing_to_strip(tmp_path):
    set_theme()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    with pytest.warns(UserWarning, match="no headline artists"):
        save_deck_variant(fig, tmp_path / "bare.png")
