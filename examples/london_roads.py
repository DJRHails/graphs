# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica: When is the worst time to be on the road in London? (The Economist).

Heatmap of additional travel time versus traffic-free conditions, 2018, %,
by day of week (rows) and hour of day (columns). Values were read off the
original's seven-bin colour scale (0-70%), so each cell carries its bin
midpoint. Weekday rush hours (08:00-09:00 and 16:00-19:00) are darkest;
nights are near-free-flowing; weekends skip the morning peak.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from graphs import C_LABEL, C_SPINE, finalize, footnotes, save_chart, set_theme, subplots

set_theme()

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Additional time in traffic vs free-flow, % — bin midpoints sampled from the
# original chart's 0-70% legend (TomTom Traffic Index / IFS, 2018).
EXTRA_TIME = np.array([
    [5, 5, 5, 5, 5, 5, 25, 55, 65, 45, 35, 35, 35, 35, 35, 45, 45, 55, 45, 25, 15, 15, 15, 5],
    [5, 5, 5, 5, 5, 5, 25, 55, 65, 45, 35, 35, 35, 35, 35, 45, 55, 65, 55, 35, 25, 15, 15, 15],
    [5, 5, 5, 5, 5, 5, 25, 55, 65, 45, 35, 35, 35, 35, 35, 55, 55, 65, 55, 35, 25, 15, 15, 15],
    [5, 5, 5, 5, 5, 5, 25, 55, 65, 45, 35, 35, 45, 35, 45, 55, 65, 65, 55, 35, 25, 15, 25, 15],
    [15, 5, 5, 5, 5, 5, 15, 35, 45, 35, 35, 45, 45, 45, 45, 65, 65, 65, 55, 35, 25, 25, 25, 25],
    [15, 15, 5, 5, 5, 5, 5, 5, 15, 25, 35, 45, 45, 45, 45, 35, 35, 35, 35, 35, 25, 25, 25, 25],
    [15, 15, 5, 5, 5, 5, 5, 5, 5, 15, 15, 25, 35, 35, 35, 35, 35, 35, 35, 25, 25, 15, 15, 5],
])  # fmt: skip

# Seven-step red scale sampled from the original's legend strip.
BIN_COLORS = [
    "#fcdcde",
    "#fac3c6",
    "#f18986",
    "#e94e4c",
    "#e72b26",
    "#a5172c",
    "#71121d",
]
BOUNDS = list(range(0, 80, 10))
CMAP = ListedColormap(BIN_COLORS)
NORM = BoundaryNorm(BOUNDS, CMAP.N)

fig, ax = subplots("daily", height=4.3)

ax.pcolormesh(
    np.arange(25),
    np.arange(8),
    EXTRA_TIME,
    cmap=CMAP,
    norm=NORM,
    edgecolors="white",
    linewidth=0.8,
)
ax.set_xlim(0, 24)
ax.set_ylim(7, 0)  # Mon at the top

ax.set_yticks(np.arange(7) + 0.5)
ax.set_yticklabels(DAYS, ha="left")
ax.yaxis.set_tick_params(pad=27)  # flush-left day labels, as in the original
ax.set_xticks([])
ax.tick_params(left=False)
ax.grid(False)

# Time-of-day labels along the top of the grid, with short tick marks.
TIME_TICKS = [
    (0.5, "00:00-01:00", "left"),
    (12.5, "12:00-13:00", "center"),
    (23.5, "23:00-00:00", "right"),
]
for x_pos, label, ha in TIME_TICKS:
    x_frac = x_pos / 24
    ax.plot(
        [x_frac, x_frac],
        [1.008, 1.032],
        transform=ax.transAxes,
        color=C_LABEL,
        linewidth=0.8,
        clip_on=False,
    )
    ax.text(
        x_frac,
        1.042,
        label,
        transform=ax.transAxes,
        ha=ha,
        va="bottom",
        fontsize=8.5,
        color=C_LABEL,
    )
ax.text(
    0.5,
    1.135,
    "Time of day",
    transform=ax.transAxes,
    ha="center",
    va="bottom",
    fontsize=9.5,
    color=C_SPINE,
)

finalize(
    ax,
    title="When is the worst time to be on the road in London?",
    descriptor="Additional time spent in traffic compared\nwith traffic-free conditions, 2018, %",
    source="",
    y_axis_right=False,
    autoscale_y=False,
    y_start=0.135,
    title_x=0.02,
)
# Restore the bespoke left/right/bottom margins after finalize (left day labels
# need the wide left gutter; the manual top band rides finalize's auto top, so
# leave top to finalize to keep the title-stack attached).
fig.subplots_adjust(bottom=0.125, left=0.085, right=0.96)
ax.spines["bottom"].set_visible(False)

# Discrete colour-scale legend, top right, aligned with the descriptor block.
bbox = ax.get_position()
leg_w, leg_h = 0.36, 0.020
leg_ax = fig.add_axes((bbox.x1 - leg_w, bbox.y1 + 0.13, leg_w, leg_h))
for i, color in enumerate(BIN_COLORS):
    leg_ax.axvspan(i * 10, (i + 1) * 10, color=color)
leg_ax.set_xlim(0, 70)
leg_ax.set_xticks([])
leg_ax.set_yticks([])
for spine in leg_ax.spines.values():
    spine.set_visible(False)
for bound in BOUNDS:
    x_frac = bound / 70
    leg_ax.plot(
        [x_frac, x_frac],
        [0, 1.45],
        transform=leg_ax.transAxes,
        color="#6e6e6e",
        linewidth=1.0,
        clip_on=False,
    )
    leg_ax.text(
        x_frac,
        1.65,
        str(bound),
        transform=leg_ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=8.5,
        color=C_LABEL,
    )

footnotes(fig, source="Sources: TomTom Traffic Index; Institute for Fiscal Studies")

save_chart(__file__)
