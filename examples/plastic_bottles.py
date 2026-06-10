# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Where do most of the plastic bottles
in the ocean come from?" daily chart.

Stacked percentage bars trace the origin of plastic bottles washed up
on Inaccessible Island, a remote speck in the South Atlantic, across
three beach surveys (1989, 2009, 2018). South America's share collapses
while Asia's surges — most of it merchant shipping waste, not river
litter. A circular locator map sits under the category legend, matching
the original's left column. Shares are read off the published chart.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

from graphs import PALETTE, finalize, footnotes, set_theme, top_legend

set_theme()

C_AFRICA = "#BA95A1"  # lighter tint of the palette purple
C_OTHER_LIGHT = "#BEC7C9"  # pale grey for the "Other regions" bucket
C_SEA = "#E4E9EB"
C_LAND = "#9FB0B8"

YEARS = ["1989", "2009", "2018"]

# (name, colour, % of total per survey year) — read off the published chart.
SERIES = [
    ("South America", PALETTE["blue"], [67, 41, 20]),
    ("Asia", PALETTE["cyan"], [9, 44, 74]),
    ("Europe", PALETTE["purple"], [6, 4, 2]),
    ("Africa", C_AFRICA, [11, 5, 2]),
    ("Other regions", C_OTHER_LIGHT, [7, 6, 2]),
]

fig, ax = plt.subplots(figsize=(5.2, 5.2))
fig.subplots_adjust(top=0.72, bottom=0.16, left=0.33, right=0.93)

bottom = np.zeros(len(YEARS))
for name, color, shares in SERIES:
    vals = np.array(shares, dtype=float)
    ax.bar(YEARS, vals, 0.72, bottom=bottom, color=color, label=name,
           edgecolor="none", zorder=2)
    # White in-bar labels for the two dominant series, centred per segment.
    if name in ("South America", "Asia"):
        for i, v in enumerate(shares):
            ax.text(i, bottom[i] + v / 2, f"{v}", ha="center", va="center",
                    color="white", fontsize=9.5, fontweight="medium", zorder=3)
    bottom += vals

ax.set_ylim(0, 100)
ax.set_yticks(range(0, 101, 20))
ax.tick_params(axis="x", length=0)

finalize(
    ax,
    title="Where do most of the plastic bottles in the ocean come from?",
    marker="rule",
    descriptor="Origin of plastic bottles found on Inaccessible Island\n% of total",
    source="",
    title_x=0.02,
    autoscale_y=False,
    auto_layout=False,
)

# Vertical category key in the left column, flush with the chart top.
handles, labels = ax.get_legend_handles_labels()
top_legend(fig, handles, labels, x=0.02, ncol=1, anchor_to=ax, fontsize=8)

# Circular locator map: the South Atlantic with the island picked out in red.
ax_map = fig.add_axes((0.015, 0.16, 0.26, 0.26))
ax_map.set_xlim(-1, 1)
ax_map.set_ylim(-1, 1)
ax_map.set_aspect("equal")
ax_map.set_xticks([])
ax_map.set_yticks([])
ax_map.axis("off")
sea = mpatches.Circle((0, 0), 0.97, facecolor=C_SEA, edgecolor=C_LAND,
                      linewidth=0.8)
ax_map.add_patch(sea)
# Abstract coastlines: South America's cone (left) and Africa (upper right),
# both clipped to the circular sea.
south_america = mpatches.Polygon(
    [(-1.0, 0.65), (-0.68, 0.45), (-0.55, 0.05), (-0.70, -0.45),
     (-0.90, -0.70), (-1.0, -0.60)],
    closed=True, facecolor=C_LAND, edgecolor="none")
africa = mpatches.Polygon(
    [(1.0, 0.95), (0.55, 0.85), (0.48, 0.55), (0.68, 0.2), (1.0, 0.1)],
    closed=True, facecolor=C_LAND, edgecolor="none")
for land in (south_america, africa):
    land.set_clip_path(sea)
    ax_map.add_patch(land)
# Faint dashed graticule arc around the island, as on the original locator.
graticule = mpatches.Circle((0.02, 0.18), 0.42, facecolor="none",
                            edgecolor=C_LAND, alpha=0.7, linewidth=0.5,
                            linestyle=(0, (2, 2)))
graticule.set_clip_path(sea)
ax_map.add_patch(graticule)
ax_map.plot([0.02], [0.18], marker="o", markersize=3, color=PALETTE["red"],
            clip_on=False)
ax_map.text(0, -0.18, "Inaccessible\nIsland", ha="center", va="center",
            color=PALETTE["red"], fontsize=8, fontweight="medium",
            linespacing=1.2)

footnotes(fig, source="Source: [PNAS](https://www.pnas.org/doi/10.1073/pnas.1909816116)")

out = Path(__file__).resolve().parent / "plastic_bottles.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved plastic-bottles chart")
