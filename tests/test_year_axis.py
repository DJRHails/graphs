"""year_axis labels the leftmost visible year in full and the rest 'YY, and the figure pickles."""

import datetime
import pickle

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from graphs import year_axis


def _dated_axes():
    fig, ax = plt.subplots()
    start = mdates.date2num(datetime.date(2021, 3, 1))
    end = mdates.date2num(datetime.date(2025, 9, 1))
    ax.plot([start, end], [0, 1])
    ax.set_xlim(start, end)
    return fig, ax


def _labels(fig, ax) -> list[str]:
    """The labels of the ticks inside the view — matplotlib also labels, but never draws, the
    locator's ticks just outside it."""
    fig.canvas.draw()
    x_lo, x_hi = ax.get_xlim()
    return [
        label.get_text()
        for tick, label in zip(ax.get_xticks(), ax.get_xticklabels(), strict=True)
        if x_lo <= tick <= x_hi
    ]


def test_leftmost_year_in_full_the_rest_abbreviated() -> None:
    fig, ax = _dated_axes()
    year_axis(ax)
    labels = _labels(fig, ax)
    assert labels[0] == "2022"
    assert labels[1:] == ["’23", "’24", "’25"]
    plt.close(fig)


def test_abbreviate_off_prints_every_year_in_full() -> None:
    fig, ax = _dated_axes()
    year_axis(ax, abbreviate=False)
    assert _labels(fig, ax) == ["2022", "2023", "2024", "2025"]
    plt.close(fig)


def test_a_year_axis_figure_pickles_and_keeps_its_labels() -> None:
    fig, ax = _dated_axes()
    year_axis(ax)
    clone = pickle.loads(pickle.dumps(fig))
    assert _labels(clone, clone.axes[0]) == _labels(fig, ax)
    plt.close(fig)
    plt.close(clone)
