# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: estimated nuclear-warhead inventories, October 2025.

Replicates The Economist's daily chart accompanying "A more complex arms
race than that of the cold war looms": stacked horizontal bars per country
split into Deployed / Reserve / Retired, x-axis on top, with a dashed
forecast box marking the US DoW projection that China will field ~1,000
warheads by 2030. Data: Federation of American Scientists estimates.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from matplotlib.patches import Patch, Rectangle

from graphs import (
    C_GRID,
    C_LABEL,
    C_RED_BRAND,
    C_SPINE,
    finalize,
    footnotes,
    save_chart,
    set_theme,
    subplots,
    top_legend,
    x_axis_top,
)

set_theme()

# Sampled from the original chart (FAS uses these in the source graphic too).
C_DEPLOYED = C_RED_BRAND
C_RESERVE = "#FBA594"
C_RETIRED = "#989583"

countries = [
    "Russia",
    "United States",
    "China",
    "France",
    "Britain",
    "India",
    "Pakistan",
    "Israel",
    "North Korea",
]
deployed = np.array([1718, 1770, 0, 280, 120, 0, 0, 0, 0])
reserve = np.array([2591, 1938, 600, 10, 105, 180, 170, 90, 50])
retired = np.array([1150, 1477, 0, 0, 0, 0, 0, 0, 0])

# Narrow portrait canvas to match the original daily-chart proportions
# (~0.77 w/h), so typography and bar thickness read at the same scale.
fig, ax = subplots("daily", height=6.0)

y = np.arange(len(countries))
ax.barh(y, deployed, height=0.68, color=C_DEPLOYED, label="Deployed", zorder=2)
ax.barh(
    y, reserve, height=0.68, left=deployed, color=C_RESERVE, label="Reserve", zorder=2
)
ax.barh(
    y,
    retired,
    height=0.68,
    left=deployed + reserve,
    color=C_RETIRED,
    label="Retired",
    zorder=2,
)
ax.invert_yaxis()

# bar_h conventions, applied manually for the stacked variant: country labels
# flush-left in a left-edge column, x-axis on top, vertical gridlines only.
ax.spines[["top", "left", "right", "bottom"]].set_visible(False)
ax.set_yticks(y)
ax.set_yticklabels(countries, ha="left", fontsize=9, color=C_LABEL)
longest = max(len(c) for c in countries)
ax.yaxis.set_tick_params(length=0, pad=longest * 9 * 0.55 + 8)
ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=0)
ax.grid(axis="y", visible=False)
ax.set_axisbelow(True)

ax.set_xlim(0, 6000)
ax.set_xticks([0, 2000, 4000, 6000])
ax.set_xticklabels(["0", "2,000", "4,000", "6,000"])
ax.axvline(0, color=C_SPINE, linewidth=1.0, zorder=3)

# Per-country totals for the small arsenals, left-aligned on a shared column.
for i, total in enumerate(deployed + reserve + retired):
    if total <= 300:
        ax.text(
            400, y[i], f"{total:,}", ha="left", va="center", fontsize=9, color=C_LABEL
        )

# The original knocks gridlines out of the bars in the background colour.
totals = deployed + reserve + retired
for gx in (2000, 4000):
    for i, total in enumerate(totals):
        if gx < total:
            ax.plot(
                [gx, gx],
                [y[i] - 0.34, y[i] + 0.34],
                color="white",
                linewidth=0.7,
                zorder=4,
            )

# Dashed forecast box on the China row: the US DoW projects ~1,000 warheads
# by 2030 — the box extends China's bar from today's 600 to that mark.
china = countries.index("China")
ax.add_patch(
    Rectangle(
        (600, china - 0.34),
        400,
        0.68,
        facecolor="white",
        edgecolor="none",
        zorder=3,
    )
)
# Dashed on top/right/bottom only — the box continues the bar, so the
# left side (where it meets today's 600) stays open.
dash = dict(
    color=C_SPINE, linewidth=1.0, linestyle=(0, (3, 2)), zorder=3, clip_on=False
)
ax.plot([600, 1000], [china - 0.34, china - 0.34], **dash)
ax.plot([600, 1000], [china + 0.34, china + 0.34], **dash)
ax.plot([1000, 1000], [china - 0.34, china + 0.34], **dash)
ax.text(
    1200,
    china,
    "US DoW forecast for 2030",
    ha="left",
    va="center",
    fontsize=9,
    fontweight="bold",
    color=C_SPINE,
)

finalize(
    ax,
    title="A more complex arms race than that of the cold war looms",
    descriptor="Estimated nuclear-warhead inventories, Oct 2025",
    source="",
    y_axis_right=False,
    title_x=0.02,
    y_start=0.13,
    autoscale_y=False,
)

# finalize's auto-layout overwrites top/bottom/left/right; restore the bespoke
# wide-left margin (for the country labels) and tight bottom here, leaving the
# auto top untouched so the title-stack anchor stays put.
fig.subplots_adjust(left=0.24, right=0.96, bottom=0.065)

# Applied after finalize() — it pins the title directly above any top-mounted
# tick labels, which would leave no room for the legend row between title and axis.
x_axis_top(ax)

handles = [
    Patch(facecolor=C_DEPLOYED, label="Deployed"),
    Patch(facecolor=C_RESERVE, label="Reserve"),
    Patch(facecolor=C_RETIRED, label="Retired"),
]
# Sit the legend in the band between the descriptor and the top-mounted x-ticks.
# Re-read the axes top AFTER the subplots_adjust above so it tracks the auto top;
# the offset clears the top-mounted x-tick labels (~0.036 above the axes top).
fig.canvas.draw()
legend_top = ax.get_position().y1 + 0.085
top_legend(
    fig,
    handles,
    [h.get_label() for h in handles],
    y=legend_top,
    ncol=3,
    handlelength=0.9,
)

# Pin the source-line top explicitly: the default (axes y0 - 0.06) would
# drop the 9pt text below the figure with this chart's tight bottom margin.
footnotes(
    fig,
    source="Sources: Federation of American Scientists; US Department of War",
    y=0.035,
)

save_chart(__file__)
