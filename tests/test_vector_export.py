"""save_chart(formats=…): vector output keeps text as text, deck variant included."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import FuncFormatter

from graphs import finalize, save_chart, set_theme, subplots, y_axis_label

TITLE = "How do the cues compare?"


def _chart():
    set_theme()
    _, ax = subplots("manuscript", height=2.8)
    ax.plot(np.arange(5), np.arange(5) * 2.0)
    finalize(ax, title=TITLE, descriptor="Accuracy, %", source="Source: test")


def test_pdf_embeds_truetype_not_type3(tmp_path):
    _chart()
    script = tmp_path / "chart.py"
    first = save_chart(script, formats=("png", "pdf"), verbose=False)

    assert first == tmp_path / "chart.png"
    assert first.is_file()
    pdf = (tmp_path / "chart.pdf").read_bytes()
    assert b"/Type3" not in pdf  # glyph outlines: text is no longer text
    assert b"/FontFile2" in pdf  # embedded TrueType: selectable text


def test_svg_keeps_text_elements(tmp_path):
    _chart()
    save_chart(tmp_path / "chart.py", formats=("svg",), verbose=False)
    svg = (tmp_path / "chart.svg").read_text()
    assert "<text" in svg
    assert TITLE.split()[0] in svg


def test_deck_variant_written_per_format(tmp_path):
    _chart()
    save_chart(tmp_path / "chart.py", deck=True, formats=("png", "pdf"), verbose=False)
    for name in ("chart.png", "chart.pdf", "chart_deck.png", "chart_deck.pdf"):
        assert (tmp_path / name).is_file(), name


def test_deck_formats_on_an_unpicklable_figure(tmp_path):
    """A lambda formatter defeats the pickle clone, so the strip runs in place —
    once, not per format: every format gets the stripped chart, no warning."""
    set_theme()
    _, ax = subplots("manuscript", height=2.8)
    ax.plot(np.arange(5), np.arange(5) * 2.0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0f}"))
    y_axis_label(ax, "flag rate", unit="%")
    finalize(ax, title=TITLE, descriptor="Accuracy, %", source="Source: test")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        save_chart(tmp_path / "chart.py", deck=True, formats=("png", "svg"), verbose=False)
    deck_warnings = [w for w in caught if "save_deck_variant" in str(w.message)]
    assert deck_warnings == []
    full = (tmp_path / "chart.svg").read_text()
    deck = (tmp_path / "chart_deck.svg").read_text()
    assert "flag rate" in full and "flag rate" in deck
    assert TITLE.split()[0] in full
    assert TITLE.split()[0] not in deck


def test_empty_formats_rejected(tmp_path):
    _chart()
    with pytest.raises(ValueError, match="formats is empty"):
        save_chart(tmp_path / "chart.py", formats=())
    plt.close("all")
