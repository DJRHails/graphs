"""y_labels_on_grid — gridline extensions under right-side labels."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, y_labels_on_grid


@pytest.fixture
def finalized_ax():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot([2000, 2010, 2020], [0, 50, 100])
    finalize(ax, title="Test", descriptor="Things, %")
    yield ax
    plt.close(fig)


def _gid_artists(ax):
    return [
        a for a in list(ax.lines) + list(ax.texts) if a.get_gid() == "y-labels-on-grid"
    ]


def test_extensions_and_labels_added(finalized_ax):
    ax = finalized_ax
    n_ticks = len(
        [
            loc
            for loc, lab in zip(ax.get_yticks(), ax.get_yticklabels())
            if lab.get_text() and min(ax.get_ylim()) <= loc <= max(ax.get_ylim())
        ]
    )
    y_labels_on_grid(ax)
    texts = [a for a in _gid_artists(ax) if a in ax.texts]
    lines = [a for a in _gid_artists(ax) if a in ax.lines]
    assert len(texts) == n_ticks
    assert len(lines) >= 1
    # Labels are right-aligned on their lines, native labels hidden.
    assert all(t.get_ha() == "right" and t.get_va() == "bottom" for t in texts)
    # Native right-side labels are switched off in favour of the gid texts.
    assert ax.yaxis.get_tick_params().get("labelright") is False
    # All extensions end at the same right edge, past the axes.
    assert len({line.get_xdata()[1] for line in lines}) == 1
    assert next(iter({line.get_xdata()[1] for line in lines})) > 1.0


def test_idempotent_recall(finalized_ax):
    ax = finalized_ax
    y_labels_on_grid(ax)
    first = len(_gid_artists(ax))
    y_labels_on_grid(ax)
    assert len(_gid_artists(ax)) == first


def test_left_side_labels_extend_leftward():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot([2000, 2010, 2020], [0, 50, 100])
    finalize(ax, title="Test", descriptor="Things, %", y_axis_right=False)
    y_labels_on_grid(ax)
    lines = [a for a in _gid_artists(ax) if a in ax.lines]
    texts = [a for a in _gid_artists(ax) if a in ax.texts]
    assert lines and texts
    # Extensions run leftward from the axes edge into negative axes-x.
    assert all(line.get_xdata()[1] < 0.0 for line in lines)
    assert all(t.get_ha() == "left" for t in texts)
    plt.close(fig)
