"""dark_zero_line rules zero only on a genuine straddle, not cosmetic ylim padding.

Regression: an all-non-negative chart given breathing room below the baseline
(``set_ylim(-0.01, ...)``) used to satisfy ``y_lo < 0 < y_hi`` and get the 0-gridline
recoloured to the dark spine — doubling the black bottom-spine baseline.
"""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest
from matplotlib.colors import to_rgba

from graphs import dark_zero_line, set_theme


@pytest.fixture(autouse=True)
def _theme():
    set_theme()


def _gridline_at(ax, y: float):
    """The visible y-gridline at ``y`` (within tick tolerance), or ``None``."""
    for loc, g in zip(ax.get_yticks(), ax.get_ygridlines()):
        if abs(loc - y) < 1e-9 and g.get_visible():
            return g
    return None


def test_cosmetic_negative_padding_does_not_rule_zero():
    """All-non-negative data + a padded y-limit below 0 → no dark zero rule."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 4], [0.05, 0.10, 0.30])
    ax.set_ylim(-0.01, 0.40)  # cosmetic breathing room, not a straddle
    fig.canvas.draw()

    n_lines_before = len(ax.lines)
    zero_grid = _gridline_at(ax, 0.0)
    sibling = _gridline_at(ax, 0.10) or _gridline_at(ax, 0.20)
    dark_zero_line(ax)

    assert len(ax.lines) == n_lines_before  # no fallback axhline added
    if zero_grid is not None and sibling is not None:
        # the 0-gridline is left as an ordinary (light) gridline, not darkened
        assert to_rgba(zero_grid.get_color()) == to_rgba(sibling.get_color())


def test_genuine_straddle_rules_zero():
    """Data with real negative values → the zero baseline is ruled dark."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 4], [-0.20, 0.10, 0.30])
    ax.set_ylim(-0.30, 0.40)  # genuine +/- range (negative y-ticks present)
    fig.canvas.draw()

    n_lines_before = len(ax.lines)
    zero_grid = _gridline_at(ax, 0.0)
    sibling = _gridline_at(ax, 0.10) or _gridline_at(ax, 0.20)
    dark_zero_line(ax)

    darkened = (
        zero_grid is not None
        and sibling is not None
        and to_rgba(zero_grid.get_color()) != to_rgba(sibling.get_color())
    )
    added_axhline = len(ax.lines) > n_lines_before
    assert darkened or added_axhline
