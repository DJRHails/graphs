"""A two-level x-axis: labelled minor ticks hang below the majors and must be reserved."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from graphs import finalize, set_theme, subplots

SOURCE = "Source: test (N=6); test_minor_tick_band.py"


def test_source_line_clears_minor_tick_labels():
    set_theme()
    fig, ax = subplots("manuscript", height=3.0)
    ax.bar(range(6), [1, 2, 3, 3, 2, 1])
    ax.set_xticks(range(6), ["a", "b", "c", "d", "e", "f"])
    # Off the major positions: matplotlib drops minor ticks that overlap a major.
    ax.set_xticks([1.5, 4.5], ["Group one", "Group two"], minor=True)
    ax.tick_params(axis="x", which="minor", length=0, pad=30)
    finalize(ax, title="Two-level axis", descriptor="Count", source=SOURCE)
    fig.canvas.draw()

    renderer = fig.canvas.get_renderer()
    minor_bottom = min(
        tl.get_window_extent(renderer).y0 for tl in ax.get_xticklabels(minor=True)
    )
    source = next(t for t in fig.texts if t.get_text().startswith("Source:"))
    assert source.get_window_extent(renderer).y1 < minor_bottom
    plt.close(fig)


def test_finalize_source_seats_below_the_lowest_row():
    set_theme()
    fig, axes = subplots("manuscript", height=4.0, nrows=2, ncols=2)
    for ax in axes.flat:
        ax.bar(range(3), [1, 2, 3])
        # No x tick labels: nothing on the lowest row drags the source down,
        # so only the anchor choice decides where it lands.
        ax.set_xticks([])
    finalize(axes[0, 0], title="Grid", descriptor="Count", source=SOURCE)
    fig.canvas.draw()

    renderer = fig.canvas.get_renderer()
    source = next(t for t in fig.texts if t.get_text().startswith("Source:"))
    lowest_row_bottom = min(ax.get_window_extent(renderer).y0 for ax in axes[1])
    assert source.get_window_extent(renderer).y1 < lowest_row_bottom
    plt.close(fig)
