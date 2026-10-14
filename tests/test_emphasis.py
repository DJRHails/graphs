"""row_emphasis / column_emphasis: spacing groups a panel grid."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from graphs import column_emphasis, finalize, row_emphasis, set_theme, subplots


def _grid(emphasis=None):
    set_theme()
    fig, axes = subplots("wide", height=4.4, nrows=3, ncols=4, sharex=True, sharey=True)
    for ax in axes.flat:
        ax.plot(np.arange(5), np.arange(5))
    if emphasis is not None:
        emphasis(fig)
    finalize(axes[0, 0], title="Grid", descriptor="Value", source="Source: test")
    return fig, axes


def _gaps_in(fig, axes) -> tuple[float, float]:
    """(gap between columns, gap between rows), in inches."""
    a, right, below = (ax.get_position() for ax in (axes[0, 0], axes[0, 1], axes[1, 0]))
    col_gap = (right.x0 - a.x1) * fig.get_figwidth()
    row_gap = (a.y0 - below.y1) * fig.get_figheight()
    return col_gap, row_gap


def test_row_emphasis_widens_only_the_row_gap():
    base_col, base_row = _gaps_in(*_grid())
    col_gap, row_gap = _gaps_in(*_grid(row_emphasis))
    plt.close("all")
    assert col_gap == pytest.approx(base_col, abs=0.01)
    # Out-spaces the within-row gap by the emphasis gap (18pt = 0.25in), even
    # though this grid's column gaps already hold the primary axes' labels.
    assert row_gap == pytest.approx(max(base_col, base_row) + 0.25, abs=0.01)


def test_column_emphasis_widens_only_the_column_gap():
    base_col, base_row = _gaps_in(*_grid())
    col_gap, row_gap = _gaps_in(*_grid(column_emphasis))
    plt.close("all")
    assert row_gap == pytest.approx(base_row, abs=0.01)
    assert col_gap == pytest.approx(max(base_col, base_row) + 0.25, abs=0.01)


def test_emphasis_needs_something_to_separate():
    set_theme()
    fig, _ = subplots("wide", ncols=3)
    with pytest.raises(ValueError, match=r"row_emphasis needs at least two rows.*1x3"):
        row_emphasis(fig)
    column_emphasis(fig)
    plt.close("all")


def test_too_short_a_figure_fails_loudly():
    set_theme()
    fig, axes = subplots("wide", height=1.4, nrows=4, ncols=2)
    row_emphasis(fig)
    with pytest.raises(ValueError, match=r"row_emphasis: .*no room for the panels"):
        finalize(axes[0, 0], title="Grid", descriptor="Value", source="Source: test")
    plt.close("all")


def test_one_grouping_per_grid():
    set_theme()
    fig, _ = subplots("wide", nrows=2, ncols=2)
    row_emphasis(fig)
    with pytest.raises(ValueError, match=r"column_emphasis: figure already has row_emphasis\("):
        column_emphasis(fig)
    plt.close("all")
