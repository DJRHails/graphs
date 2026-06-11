# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: Economist daily chart on where Christianity is growing.

Slope chart of the world Christian population split by region — each
region is a single 2015 → 2060 (forecast) segment with endpoint dots and
value labels at both ends. Sub-Saharan Africa carries the accent red and
a heavier line; everything else recedes into blues and greys. Region
names sit directly on the lines, so no legend is needed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import C_GRID, PALETTE, finalize, set_theme

set_theme()

# Pew Research: regional share of the world's Christians, % of total.
# (name, 2015, 2060 forecast, colour, linewidth)
SERIES = [
    ("Sub-Saharan Africa", 26, 42, PALETTE["red"], 2.6),
    ("Latin America", 25, 22, "#76A0B6", 1.8),
    ("Europe", 24, 14, "#B0BCC3", 1.8),
    ("Asia-Pacific", 13, 13, PALETTE["blue"], 1.8),
    ("North America", 12, 9, PALETTE["grey"], 1.8),
    ("Middle East and north Africa", 1, 1, PALETTE["cyan"], 1.8),
]

X_LEFT, X_RIGHT = 2015, 2060

fig, ax = plt.subplots(figsize=(5.0, 5.3))

# Two vertical gridlines anchor the slope chart — no horizontal grid.
for x in (X_LEFT, X_RIGHT):
    ax.axvline(x, color=C_GRID, linewidth=1.0, zorder=0)

for name, v0, v1, color, lw in SERIES:
    is_red = color == PALETTE["red"]
    ax.plot(
        [X_LEFT, X_RIGHT],
        [v0, v1],
        color=color,
        linewidth=lw,
        marker="o",
        markersize=7.0 if is_red else 6.0,
        zorder=4 if is_red else 3,
        solid_capstyle="round",
    )

# Endpoint value labels, nudged apart where values stack (26/25/24 on the
# left, 14/13 on the right) so the digits never collide.
_left_nudge = {26: 27.1, 25: 24.9, 24: 22.6, 13: 13.4, 12: 11.2}
_right_nudge = {14: 14.8, 13: 12.7}
for name, v0, v1, color, _ in SERIES:
    ax.text(
        X_LEFT - 1.6,
        _left_nudge.get(v0, v0),
        str(v0),
        color=color,
        fontsize=10,
        fontweight="bold",
        ha="right",
        va="center",
        zorder=6,
    )
    ax.text(
        X_RIGHT + 1.6,
        _right_nudge.get(v1, v1),
        str(v1),
        color=color,
        fontsize=10,
        fontweight="bold",
        ha="left",
        va="center",
        zorder=6,
    )

# Region names sit directly on the chart, coloured to match their lines.
# (text, x, y, ha) — positions mirror the reference layout.
_name_labels = [
    ("Sub-Saharan Africa", 2043, 33.2, "center"),
    ("Latin America", 2038, 25.7, "center"),
    ("Europe", 2051, 18.8, "center"),
    ("Asia-Pacific", 2017, 15.0, "left"),
    ("North America", 2043, 7.9, "center"),
    ("Middle East and north Africa", 2017, 3.0, "left"),
]
_colors = {name: color for name, _, _, color, _ in SERIES}
for text, lx, ly, ha in _name_labels:
    ax.text(
        lx,
        ly,
        text,
        color=_colors[text],
        fontsize=10,
        fontweight="bold",
        ha=ha,
        va="center",
        zorder=6,
    )

ax.set_xlim(2009.5, 2065.5)
ax.set_ylim(0, 44)
ax.set_xticks([X_LEFT, X_RIGHT])
ax.set_xticklabels(["2015", "2060 forecast"], fontsize=10)
ax.set_yticks([])
ax.grid(visible=False)
ax.tick_params(axis="x", length=0, pad=6)
for spine in ax.spines.values():
    spine.set_visible(False)

finalize(
    ax,
    title="Sub-Saharan Africa is the biggest area of expansion for Christianity",
    descriptor="World Christian population\n% of total",
    source="Source: Pew Research",
    autoscale_y=False,
)

out = Path(__file__).resolve().parent / "christianity.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved christianity chart")
