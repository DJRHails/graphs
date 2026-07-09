"""The patterns the touchstone deck-variant program repeated, now first-class."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import (
    finalize,
    footnotes,
    panel_label,
    save_chart,
    save_deck_variant,
    set_theme,
    subplots,
    top_legend,
    y_axis_label,
)


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _tagged(fig):
    return [t.get_text() for t in fig.texts if getattr(t, "_graphs_deck_strip", False)]


def test_footnotes_single_note_no_source_is_tagged():
    # The legacy packed path (one note, no source=) leaked into deck variants.
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1])
    finalize(ax, title="T", source="Source: somewhere")
    footnotes(fig, "Profiled by Claude Opus 4.8; one label per conversation.", verify=False)
    assert any("Profiled by" in t for t in _tagged(fig))


def test_top_legend_accepts_axes_shorthand():
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1], label="a series")
    leg = top_legend(ax, ncol=1)
    assert [t.get_text() for t in leg.get_texts()] == ["a series"]
    assert leg.figure is fig


def test_top_legend_axes_shorthand_requires_labels_somewhere():
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1], label="s")
    with pytest.raises(ValueError, match="handles\\+labels"):
        top_legend(fig)  # figure first-arg but no handles/labels


def test_left_marker_clears_panel_label_band():
    fig, ax = subplots("daily", height=3.4)
    ax.plot([0, 1], [0, 1])
    y_axis_label(ax, "rate", unit="%", side="left")
    finalize(ax, title="T", source="Source: x", panel_labels=True)
    panel_label(ax, "Heading")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    spec = fig._graphs_y_axis_labels[0]
    label_bottom = min(
        a.get_window_extent(renderer=renderer).transformed(inv).y0 for a in spec.artists
    )
    heading = next(t for t in fig.texts if t.get_text() == "Heading")
    heading_top = heading.get_window_extent(renderer=renderer).transformed(inv).y1
    assert label_bottom >= heading_top - 1e-9


def test_deck_variant_drops_raw_suptitle(tmp_path):
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1])
    fig.suptitle("Raw panel suptitle")
    finalize(ax, title="T", source="Source: x")
    full = tmp_path / "c.png"
    fig.savefig(full, dpi=150, bbox_inches="tight")
    deck = save_deck_variant(fig, full)
    assert deck.is_file()
    # live figure untouched (clone path)
    assert fig._suptitle.get_text() == "Raw panel suptitle"


def test_deck_variant_tolerates_manually_tagged_suptitle(tmp_path):
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1])
    sup = fig.suptitle("Tagged suptitle")
    sup._graphs_deck_strip = True  # the old manual workaround must not double-remove
    finalize(ax, title="T", source="Source: x")
    fig.savefig(tmp_path / "c.png", dpi=150, bbox_inches="tight")
    assert save_deck_variant(fig, tmp_path / "c.png").is_file()


def test_save_chart_deck_param(tmp_path):
    fig, ax = subplots("daily", height=3.0)
    ax.plot([0, 1], [0, 1])
    finalize(ax, title="T", source="Source: x")
    script = tmp_path / "myscript.py"
    script.touch()
    out = save_chart(str(script), deck=True, verbose=False)
    assert out.is_file()
    assert (tmp_path / "myscript_deck.png").is_file()
