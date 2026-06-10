# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "America's elderly seem more screen-obsessed
than the young" daily chart.

Two stacked-area panels — daily hours spent consuming media in the first
quarter of each year, 2015-19, for 18-34s and the 65+, split into TV,
smartphone and computer time. Values are read off the published chart
(Nielsen data).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from graphs import C_LABEL, C_RED_BRAND, finalize, footnotes, right_axis, set_theme

set_theme()

C_TV = C_RED_BRAND
C_PHONE = "#B4CFE0"  # pale blue — smartphone
C_COMPUTER = "#69A0B9"  # steel blue — computer

YEARS = np.array([2015, 2016, 2017, 2018, 2019])

# Hours per day, bottom-of-stack first: TV, smartphone, computer.
PANELS = [
    (
        "18-34",
        [4.0, 3.8, 3.6, 3.4, 3.2],
        [1.45, 2.0, 2.45, 3.0, 3.6],
        [0.75, 0.67, 0.61, 0.56, 0.47],
    ),
    (
        "65+",
        [7.4, 7.5, 7.55, 7.6, 7.6],
        [0.3, 0.65, 1.1, 1.5, 1.95],
        [0.5, 0.47, 0.45, 0.4, 0.36],
    ),
]

fig, axes = plt.subplots(1, 2, figsize=(5.2, 4.9), sharey=True)
fig.subplots_adjust(top=0.70, bottom=0.13, left=0.03, right=0.92, wspace=0.55)

for ax, (heading, tv, phone, computer) in zip(axes, PANELS):
    ax.stackplot(
        YEARS,
        tv,
        phone,
        computer,
        colors=[C_TV, C_PHONE, C_COMPUTER],
        linewidth=0,
        zorder=3,  # above the gridlines, like the original
    )
    ax.set_xlim(2015, 2019)
    ax.set_ylim(0, 10)
    ax.set_yticks(range(0, 11, 2))
    ax.set_xticks([2015, 2019])
    ax.set_xticklabels(["2015", "19"])
    ax.tick_params(axis="x", length=4, pad=4)
    right_axis(ax)

    # Panel heading, top-left above the plot.
    ax.text(
        0.0, 1.02, heading,
        transform=ax.transAxes, fontsize=10.5, fontweight="bold",
        color=C_LABEL, ha="left", va="bottom", zorder=6,
    )

# Direct in-area series labels on the left panel only, like the original.
ax_young = axes[0]
ax_young.text(2016.1, 1.6, "TV", color="white", fontsize=12,
              fontweight="bold", ha="center", va="center", zorder=5)
ax_young.text(2016.1, 4.75, "Smartphone", color="white", fontsize=12,
              fontweight="bold", ha="center", va="center", zorder=5)
ax_young.text(2016.4, 7.0, "Computer", color="#5E96B0", fontsize=12,
              fontweight="bold", ha="center", va="bottom", zorder=5)

finalize(
    axes[0],
    title="America's elderly seem more screen-obsessed than the young",
    descriptor="Daily hours spent consuming media\nBy age group, in the first quarter of the year",
    source="",
    marker="rule",
    title_x=0.03,
    y_start=0.075,  # leave room for the panel headings
    autoscale_y=False,
    auto_layout=False,  # side-by-side panels need explicit wspace
)
footnotes(fig, source="Source: Nielsen")

out = Path(__file__).resolve().parent / "elderly_screens.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved elderly-screens chart")
