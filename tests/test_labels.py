"""y_labels_on_grid — gridline extensions under right-side labels."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, y_labels_on_grid
from graphs._labels import _ticks_are_numeric


@pytest.fixture
def finalized_ax():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot([2000, 2010, 2020], [0, 50, 100])
    # Opt out of the finalize default so the manual helper path is what's
    # under test (test_finalize_applies_on_grid_default covers the default).
    finalize(ax, title="Test", descriptor="Things, %", y_labels="ticks")
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


def test_finalize_applies_on_grid_default():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot([2000, 2010, 2020], [0, 50, 100])
    finalize(ax, title="Test", descriptor="Things, %")
    assert _gid_artists(ax), "finalize default should apply y_labels_on_grid"
    plt.close(fig)


def test_finalize_skips_on_grid_for_categorical_axes():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.barh(["a", "b", "c"], [1, 2, 3])
    ax.grid(axis="y", visible=False)
    finalize(ax, title="Test", descriptor="Things, %")
    assert not _gid_artists(ax), "categorical axes must keep native labels"
    plt.close(fig)


@pytest.mark.parametrize(
    "labels",
    [
        ["12", "1.2k", "80%"],
        ["$40", "−3", "1,200"],
        ["2000", "2010", "2020"],
        ["0", "3B", "1.5T"],
    ],
)
def test_ticks_are_numeric_accepts_house_formats(labels):
    assert _ticks_are_numeric(labels)


@pytest.mark.parametrize(
    "labels",
    [
        ["France", "10", "20"],
        ["banked sweep\n(all pairs)", "blend re-fire"],
        ["Q1 2024", "Q2 2024"],
    ],
)
def test_ticks_are_numeric_rejects_categories(labels):
    assert not _ticks_are_numeric(labels)


def test_on_grid_skips_categorical_labels_even_with_visible_y_grid():
    """Regression: a hand-rolled categorical barh that leaves the y-grid flag on
    used to slip past finalize's gridline-visibility gate; its labels were then
    lifted onto their gridlines (``va="bottom"``), so each two-line row label
    straddled the bar above it. The label-text guard must catch it."""
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.barh([1, 0], [50, 80], height=0.5)
    ax.set_yticks([1, 0])
    ax.set_yticklabels(["banked sweep\n(all pairs)", "blend re-fire"], fontsize=8)
    ax.grid(axis="x", linewidth=0.6)  # y-grid flag left untouched (theme default)
    finalize(ax, title="Test", descriptor="Things, %", y_axis_right=False)
    assert not _gid_artists(ax), "categorical labels must keep native placement"
    assert [t.get_text() for t in ax.get_yticklabels() if t.get_text()], (
        "native tick labels must survive finalize"
    )
    plt.close(fig)


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


def test_baseline_extension_sits_at_floor_when_axis_inverted():
    """Regression: on an inverted axis (a horizontal bar chart) the dark baseline
    stub extends at the physical floor (``ylim[0]``), never stranded at the visual
    top. Previously the floor was taken as ``min(ylim)``, which is the visual *top*
    once the axis is inverted, so the stub was drawn top-right."""
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.barh([0, 1, 2, 3], [0.8, 0.7, 0.5, 0.4])
    finalize(ax, title="Test", y_labels="ticks")
    ax.set_yticks([0, 1, 2, 3])
    ax.set_ylim(-0.5, 3.5)
    ax.invert_yaxis()  # ylim -> (3.5, -0.5): the floor is 3.5, the ceiling -0.5
    y_labels_on_grid(ax)
    lines = [a for a in _gid_artists(ax) if a in ax.lines]
    tick_locs = list(ax.get_yticks())
    extension_ys = [
        float(line.get_ydata()[0])
        for line in lines
        if not any(abs(float(line.get_ydata()[0]) - t) < 1e-6 for t in tick_locs)
    ]
    floor, ceiling = ax.get_ylim()  # (3.5, -0.5) when inverted
    assert extension_ys, "expected a baseline-extension stub off the tick locations"
    assert all(abs(y - floor) < 1e-6 for y in extension_ys), (
        f"baseline stub must sit at the physical floor {floor}, got {extension_ys}"
    )
    assert not any(abs(y - ceiling) < 1e-6 for y in extension_ys), (
        f"baseline stub stranded at the visual top {ceiling}: {extension_ys}"
    )
    plt.close(fig)
