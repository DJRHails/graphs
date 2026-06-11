# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Closing the gap" age-gap snapshot chart.

Four chronological snapshots (1960, 1980, 2000, 2024) of the average
age gap between husband and wife across the wife's income percentile.
Earlier years fade into muted slate; the present-day line is the
accent red so the eye reads "today" first — this is the reusable
"chronological snapshot lines" pattern, backed by
``graphs.snapshot_palette``.

Y-axis truncates at 1.5 (no zero baseline); the ``broken_axis`` helper
draws the squiggle on the right-hand y-tick column to flag this.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as ticker
import numpy as np

from graphs import (
    C_GRID,
    C_LABEL,
    C_LABEL_MUTED,
    broken_axis,
    direction_label,
    finalize,
    footnotes,
    save_chart,
    set_theme,
    snapshot_palette,
    subplots,
)

set_theme()

# Income percentile bins on the x-axis: 0, 5, 10, ..., 95, 99.
x = np.array(
    [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99]
)

# Synthetic shapes mirroring the reference: each line drifts down across
# percentile then hooks up at the 99th. Older snapshots sit higher; the
# 2024 line is the lowest and flattest.
y_1960 = np.array(
    [
        3.80,
        3.65,
        3.78,
        3.68,
        3.60,
        3.55,
        3.62,
        3.50,
        3.48,
        3.58,
        3.40,
        3.32,
        3.30,
        3.35,
        3.30,
        3.25,
        3.28,
        3.20,
        3.22,
        3.42,
        3.50,
    ]
)
y_1980 = np.array(
    [
        2.75,
        2.78,
        2.82,
        2.80,
        2.78,
        2.85,
        2.92,
        2.88,
        2.85,
        2.90,
        2.85,
        2.80,
        2.72,
        2.68,
        2.75,
        2.78,
        2.80,
        2.78,
        2.80,
        3.00,
        3.20,
    ]
)
y_2000 = np.array(
    [
        2.50,
        2.48,
        2.55,
        2.50,
        2.45,
        2.42,
        2.45,
        2.38,
        2.45,
        2.40,
        2.38,
        2.35,
        2.32,
        2.30,
        2.32,
        2.30,
        2.32,
        2.30,
        2.35,
        2.50,
        2.62,
    ]
)
y_2024 = np.array(
    [
        2.42,
        2.45,
        2.62,
        2.50,
        2.42,
        2.40,
        2.38,
        2.30,
        2.40,
        2.38,
        2.22,
        2.15,
        2.12,
        2.18,
        2.15,
        2.18,
        2.20,
        2.15,
        2.12,
        2.12,
        2.15,
    ]
)

series = [
    ("1960", y_1960),
    ("1980", y_1980),
    ("2000", y_2000),
    ("2024", y_2024),
]
colors = snapshot_palette(len(series))

fig, ax = subplots("wide", height=4.2)

for (label, ys), color in zip(series, colors):
    lw = 2.0 if label == "2024" else 1.6
    ms = 4.2 if label == "2024" else 3.6
    ax.plot(
        x,
        ys,
        color=color,
        linewidth=lw,
        marker="o",
        markersize=ms,
        markerfacecolor=color,
        markeredgecolor=color,
        label=label,
        zorder=4 if label == "2024" else 3,
    )

# Axis cosmetics. Y-axis is truncated (1.5 → 4.0); broken_axis squiggle
# flags the non-zero baseline.
ax.set_xlim(-1.5, 100.5)
ax.set_ylim(1.5, 4.0)
ax.set_xticks(list(x))
ax.set_xticklabels([str(v) for v in x], fontsize=9)
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)
ax.tick_params(axis="x", length=0, pad=6)

ax.set_xlabel(
    "Income percentile of wife†",
    fontsize=9.5,
    color=C_LABEL,
    labelpad=8,
)

# In-chart series labels — placed manually to mirror the reference layout
# (labels float above-and-left of where each line sits at mid-chart).
_label_positions = {
    "1960": (52, 3.50),
    "1980": (52, 2.97),
    "2000": (52, 2.55),
    "2024": (52, 1.95),
}
for (label, _), color in zip(series, colors):
    lx, ly = _label_positions[label]
    ax.text(
        lx,
        ly,
        label,
        color=color,
        fontsize=11,
        fontweight="medium",
        ha="left",
        va="center",
        zorder=6,
    )

# "↑ Older husband" cue in slate, upper-right area of the plot.
direction_label(
    ax,
    "Older husband",
    xy=(0.78, 0.86),
    arrow="↑",
    color=C_LABEL_MUTED,
    fontsize=10,
)

finalize(
    ax,
    title="Closing the gap",
    descriptor="Average age gap of married couples*, by income of wife, years",
    source="Sources: [US Census Bureau](https://www.census.gov/); [The Economist](https://www.economist.com/)",
    y_axis_right=True,
    autoscale_y=False,
    footnote_lines=2,  # right-anchored footnote sits below source + xlabel
)

# Broken-axis squiggle on the right (matches the y-tick column).
broken_axis(ax, side="right")

# Footnotes sit on the same baseline as the source line, anchored on the
# right (matches the Economist reference layout for this chart).
fig.canvas.draw()
_bbox = ax.get_position()
footnotes(
    fig,
    "*Cohabiting    †Employed with an income",
    y=_bbox.y0 - 0.075,
    x=0.62,
)

save_chart(__file__)
