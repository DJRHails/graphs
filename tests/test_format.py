"""Tests for graphs.format_count and graphs.scale_axis."""

from __future__ import annotations

import pickle

import matplotlib.pyplot as plt
import pytest

from graphs import format_count, scale_axis


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "0"),
        (16, "16"),
        (64, "64"),
        (500, "500"),
        (519, "520"),       # 2 s.f.
        (999, "1k"),        # rounds up across the unit boundary
        (1234, "1.2k"),     # 2 s.f. keeps one decimal
        (2030, "2k"),       # trailing .0 stripped
        (16384, "16k"),
        (22510, "23k"),
        (1_250_000, "1.3M"),
        (3_000_000_000, "3B"),
    ],
)
def test_format_count_two_sig_figs_with_units(n: int, expected: str) -> None:
    assert format_count(n) == expected


def test_format_count_negative_keeps_sign() -> None:
    assert format_count(-1234) == "-1.2k"


def test_format_count_respects_sig_arg() -> None:
    assert format_count(16384, sig=3) == "16.4k"


def test_scale_axis_figure_pickles_and_keeps_its_labels() -> None:
    fig, ax = plt.subplots()
    ax.plot([0, 60_000])
    ax.set_ylim(0, 60_000)
    ax.set_yticks([0, 20_000, 40_000, 60_000])
    scale_axis(ax)
    clone = pickle.loads(pickle.dumps(fig))
    for figure in (fig, clone):
        figure.canvas.draw()
        labels = [label.get_text() for label in figure.axes[0].get_yticklabels()]
        assert labels == ["0", "20", "40", "60"]
    plt.close(fig)
    plt.close(clone)
