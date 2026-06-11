# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: The Arctic is warming twice as fast as the rest of the world.

The Economist's daily chart of observed 2018 temperature change by
latitude (relative to the 1951-1980 average), after Carbon Brief. A red
dot-line traces the zonal average across twelve 15-degree latitude
bands; translucent pink bars show the range across datasets; pale blue
panels band the Arctic and Antarctic. Values were read off the original
chart pixel-by-pixel.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from graphs import (
    C_RED_BRAND,
    C_GRID,
    C_LABEL,
    C_SPINE,
    finalize,
    set_theme,
    top_legend,
)

set_theme()

C_RED_LINE = C_RED_BRAND
C_RANGE = "#EE7479"  # at RANGE_ALPHA over white this gives the original's pink
C_POLAR_BAND = "#D9F0F5"
RANGE_ALPHA = 0.45

# Zonal mean temperature change, 2018 vs 1951-1980, deg C — band centres at
# 15-degree steps from 82.5N to 82.5S. Average plus min-max range across
# datasets, digitised from the original chart.
LAT = [82.5, 67.5, 52.5, 37.5, 22.5, 7.5, -7.5, -22.5, -37.5, -52.5, -67.5, -82.5]
AVG = [3.05, 2.20, 1.40, 1.10, 0.95, 0.85, 0.85, 0.75, 0.80, 0.45, 0.65, 0.70]
LO = [2.15, 0.55, -0.25, 0.20, 0.30, 0.40, 0.35, 0.15, 0.25, -0.25, -0.25, 0.15]
HI = [4.80, 3.60, 2.35, 1.90, 1.75, 1.55, 1.60, 1.45, 1.30, 1.15, 1.95, 1.15]

fig, ax = plt.subplots(figsize=(5.4, 4.5))
# Top-mounted x-ticks plus a top_legend sit between the title and the chart,
# so the standard auto_layout doesn't fit (same pattern as nuclear_warheads).
fig.subplots_adjust(top=0.70, bottom=0.155, left=0.095, right=0.965)

# Pale blue Arctic / Antarctic panels, run across the full figure width like
# the original (under the latitude labels in the left margin).
for y0, y1 in [(66.5, 90), (-90, -66.5)]:
    band = ax.axhspan(y0, y1, xmin=-0.12, xmax=1.012, color=C_POLAR_BAND, zorder=0)
    band.set_clip_on(False)

ax.barh(
    LAT,
    [h - lo for h, lo in zip(HI, LO)],
    left=LO,
    height=15,
    color=C_RANGE,
    alpha=RANGE_ALPHA,
    linewidth=0,
    zorder=2,
)
ax.plot(AVG, LAT, color=C_RED_LINE, linewidth=2.0, marker="o", markersize=6.5, zorder=5)

ax.set_xlim(-1.7, 5)
ax.set_ylim(-90, 90)
ax.set_xticks([0, 1, 2, 3, 4, 5])
ax.xaxis.tick_top()
ax.xaxis.set_tick_params(labelsize=9, length=3.5, direction="out")
ax.set_yticks([90, 45, 0, -45, -90])
ax.set_yticklabels(["90°N", "45°N", "0", "45°S", "90°S"], fontsize=9, color=C_LABEL)
ax.yaxis.set_tick_params(length=0, pad=8)

ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=1)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=1)
for grid_line, lat in zip(ax.yaxis.get_gridlines(), ax.get_yticks()):
    grid_line.set_visible(abs(lat) < 90)  # no rules along the top/bottom edges
ax.set_axisbelow(False)
ax.axvline(0, color=C_SPINE, linewidth=1.0, zorder=3)
# The original's dark zero line runs up to its top tick mark.
ax.plot([0, 0], [90, 93.5], color=C_SPINE, linewidth=1.0, clip_on=False, zorder=3)
ax.spines[["top", "left", "right", "bottom"]].set_visible(False)

# Region labels inside the plot, left of the zero line. Arctic / Antarctic sit
# dead-centre in their pale-blue bands (66.5-90 degrees), like the original.
ax.text(
    -1.05,
    78.25,
    "Arctic",
    ha="center",
    va="center",
    fontsize=9,
    color=C_SPINE,
    zorder=4,
)
ax.text(
    -1.05, 1.5, "Equator", ha="center", va="bottom", fontsize=9, color=C_SPINE, zorder=4
)
ax.text(
    -1.05,
    -78.25,
    "Antarctic",
    ha="center",
    va="center",
    fontsize=9,
    color=C_SPINE,
    zorder=4,
)

ax.text(
    2.55,
    48,
    "↑ The Arctic is\nwarming much faster\nthan everywhere else",
    ha="left",
    va="top",
    fontsize=9.5,
    fontweight="medium",
    color=C_RED_LINE,
    linespacing=1.25,
    zorder=6,
)

finalize(
    ax,
    title="The Arctic is warming twice as fast as the rest of the world",
    descriptor="Observed temperature change by latitude, °C\n2018, relative to 1951-1980 average",
    source="Source: [Carbon Brief](https://www.carbonbrief.org/)",
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
    auto_layout=False,
)


# "Latitude" column header, level with the x tick labels.
fig.canvas.draw()
bbox = ax.get_position()
fig.text(
    0.02, bbox.y1 + 0.035, "Latitude", fontsize=9, color=C_LABEL, ha="left", va="bottom"
)

handles = [
    mlines.Line2D([], [], color=C_RED_LINE, marker="o", linestyle="None", markersize=6),
    mpatches.Patch(facecolor=C_RANGE, alpha=RANGE_ALPHA),
]
top_legend(
    fig,
    handles,
    ["Average", "Range‡"],
    align="right",
    x=bbox.x1,
    y=bbox.y1 + 0.10,
    fontsize=9,
)

out = Path(__file__).resolve().parent / "arctic_warming.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Arctic warming chart")
