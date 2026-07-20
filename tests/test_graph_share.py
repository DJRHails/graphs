"""The graph-share guard: verify_graph_share warns when the graph is <75% of the image."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import (
    finalize,
    footnotes,
    graph_area_fraction,
    set_theme,
    subplots,
    verify_graph_share,
)


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _lean_chart():
    """One-line headline stack over a tall plot — comfortably graph-dominated."""
    fig, ax = subplots("daily", height=5.0)
    ax.plot([0, 1, 2], [0, 1, 4])
    finalize(ax, title="Short title", descriptor="Things, %", source="Source: x; s.py")
    return fig


def _text_heavy_chart():
    """A short plot wrapped in a multi-line title, descriptor and footnote stack."""
    fig, ax = subplots("daily", height=2.6)
    ax.plot([0, 1, 2], [0, 1, 4])
    finalize(
        ax,
        title="A very long two-line headline that states the claim and then keeps "
        "going well past the wrap point",
        descriptor="A descriptor that also runs long enough to wrap onto several "
        "lines, naming the quantity, the axis mapping, the protocol, the model "
        "and the temperature besides",
    )
    footnotes(
        fig,
        "A first footnote long enough to wrap across the figure width and then "
        "some, defining a coined term with a concrete worked example attached.",
        "A second footnote carrying the conditions, the model id, the seed table "
        "and the era of the banked draws.",
        source="Source: a dataset with a long name (N=12,345); some_script.py",
    )
    return fig


def test_fraction_measures_lean_chart_high():
    assert graph_area_fraction(_lean_chart()) >= 0.75


def test_fraction_measures_text_heavy_chart_low():
    assert 0.0 < graph_area_fraction(_text_heavy_chart()) < 0.75


def test_no_warning_on_lean_chart():
    assert verify_graph_share(_lean_chart()) is None


def test_warns_on_text_heavy_chart():
    fig = _text_heavy_chart()
    with pytest.warns(UserWarning, match="verify_graph_share"):
        msg = verify_graph_share(fig)
    assert msg is not None and "Cut figure text" in msg


def test_axesless_figure_passes_silently():
    fig = plt.figure()
    fig.text(0.5, 0.5, "no axes here")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert verify_graph_share(fig) is None


def test_custom_threshold():
    fig = _lean_chart()
    with pytest.warns(UserWarning, match="minimum 99%"):
        verify_graph_share(fig, min_fraction=0.99)
