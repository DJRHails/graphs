# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Rich and poor consumers' spending
patterns are converging" daily chart.

Two lines of global consumption spending share, 2000-2025: the richest
1% (grey) drifts down from ~13.4% while the poorest 50% (red) climbs
from ~7%, the two crossing around 2018-19. Values are approximated by
pixel-sampling the reference image. Y-axis is truncated (5.5 -> 14), so
``broken_axis`` flags the non-zero baseline with the squiggle next to
the right-hand tick column.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from graphs import (
    C_GRID,
    C_LABEL,
    C_RED,
    broken_axis,
    finalize,
    inset_tick_labels,
    save_chart,
    set_theme,
)

set_theme()

# The published chart's "Richest 1%" line is a warm grey (sampled), not
# the library's blue-tinted slate grey.
C_GREY = "#9b9a91"

years = np.arange(2000, 2026)

# Share of global consumption spending, % of total (pixel-sampled from
# the reference chart; World Data Lab is the underlying source).
richest_1pct = np.array(
    [
        13.35,
        13.35,
        13.30,
        13.30,
        13.20,
        13.20,
        13.05,
        12.75,
        12.60,
        12.30,
        12.05,
        12.00,
        11.90,
        11.80,
        11.90,
        11.90,
        11.65,
        11.45,
        11.40,
        11.25,
        11.15,
        11.25,
        11.35,
        11.25,
        11.20,
        11.10,
    ]
)
poorest_50pct = np.array(
    [
        7.00,
        7.15,
        7.40,
        7.55,
        7.70,
        7.95,
        8.10,
        8.40,
        8.65,
        9.10,
        9.30,
        9.55,
        9.80,
        10.20,
        10.40,
        10.70,
        10.95,
        11.10,
        11.20,
        11.40,
        11.60,
        11.75,
        11.70,
        11.70,
        11.75,
        11.85,
    ]
)

# Reference is ~325x428 px, so the figure keeps a w/h ratio near 0.76.
fig, ax = plt.subplots(figsize=(3.85, 5.45))

ax.plot(years, richest_1pct, color=C_GREY, linewidth=1.8, zorder=3)
# White underlay so the red line reads cleanly where it crosses the grey.
ax.plot(
    years,
    poorest_50pct,
    color=C_RED,
    linewidth=1.8,
    zorder=4,
    path_effects=[patheffects.withStroke(linewidth=3.8, foreground="white")],
)

# Direct in-chart series labels. The reference sets both in plain dark
# text (not series colours): "Richest 1%" above the grey line's descent,
# "Poorest 50%" below the red climb.
ax.text(
    2009.1,
    12.85,
    "Richest 1%",
    color=C_LABEL,
    fontsize=9.5,
    fontweight="medium",
    ha="left",
    va="center",
    zorder=6,
)
ax.text(
    2011.1,
    8.95,
    "Poorest 50%",
    color=C_LABEL,
    fontsize=9.5,
    fontweight="medium",
    ha="left",
    va="center",
    zorder=6,
)

# Axis cosmetics: truncated y (5.5 -> 14), ticks every 2; yearly minor
# ticks on x with five-year major labels 2000, 05, ..., 25.
ax.set_xlim(2000, 2025)
ax.set_ylim(5.5, 14)
ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
ax.yaxis.set_major_formatter(ticker.StrMethodFormatter("{x:.0f}"))
ax.set_xticks(np.arange(2000, 2026, 5))
ax.set_xticklabels(["2000", "05", "10", "15", "20", "25"])
ax.set_xticks(np.arange(2000, 2026, 1), minor=True)
ax.tick_params(axis="x", which="minor", length=3)
inset_tick_labels(ax, axis="x")
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)

finalize(
    ax,
    title="Rich and poor consumers’ spending patterns are converging",
    descriptor="Global consumption spending, % of total",
    source="Source: World Data Lab",
    y_axis_right=True,
    autoscale_y=False,
)

# Squiggle in the right-hand tick column (just past the axis end, under
# the "6" label) flags the truncated baseline, as in the reference.
broken_axis(ax, x=2026.3)

save_chart(__file__)
