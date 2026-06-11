# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica of *The Economist*'s "Female Uber drivers receive better tips than men".

Vertical dumbbell (lollipop-pair) chart: one column per driver age group,
a pale-blue bar connecting the male dot (slate) to the female dot (red).
Values are expected tips relative to male drivers aged 21-25, in dollars,
so the 21-25 male dot is the zero "Reference" point (ringed marker with a
leader line). Values are read off the published chart.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import (
    C_GRID,
    C_LABEL_MUTED,
    C_RED,
    C_SPINE,
    C_TEXT,
    finalize,
    set_theme,
    x_axis_label,
)

set_theme()

AGE_GROUPS = ["21-25", "26-34", "35-44", "45-54", "55-64", "65+"]
# Expected tip relative to male drivers aged 21-25, $ (read off the chart).
FEMALE = [0.043, 0.0415, 0.039, 0.022, 0.013, -0.007]
MALE = [0.0, -0.004, -0.004, -0.0095, -0.018, -0.022]

BAR_COLOR = "#cee1ea"  # pale-blue connector sampled from the reference

fig, ax = plt.subplots(figsize=(4.8, 5.0))

# Connector bars first so the dots sit on top.
for i, (f, m) in enumerate(zip(FEMALE, MALE)):
    ax.plot([i, i], [m, f], color=BAR_COLOR, linewidth=8.2, solid_capstyle="butt", zorder=2)

# Zero baseline (darker than the gridlines — it carries the "Reference" level).
ax.axhline(0, color=C_SPINE, linewidth=0.8, zorder=3)

ax.scatter(range(len(AGE_GROUPS)), FEMALE, s=105, color=C_RED, zorder=5, linewidths=0)
ax.scatter(range(len(AGE_GROUPS)), MALE, s=105, color=C_LABEL_MUTED, zorder=5, linewidths=0)
# The 21-25 male dot is the reference point: ringed marker + leader + label.
ax.scatter([0], [0], s=105, color=C_LABEL_MUTED, zorder=6, edgecolors=C_TEXT, linewidths=1.2)
ax.plot([0, 0], [-0.0045, -0.0075], color=C_TEXT, linewidth=0.8, zorder=4)
ax.text(-0.42, -0.0085, "Reference", color=C_TEXT, fontsize=9, ha="left", va="top")

# Direct series labels, placed as in the reference: "Female drivers" floats
# in the open gap above the 45-54 female dot, clear of the taller 35-44 bar.
ax.text(3.4, 0.026, "Female drivers", color=C_RED, fontsize=10.5, fontweight="bold",
        ha="center", va="center", zorder=6)
ax.text(1.55, -0.0095, "Male drivers", color=C_LABEL_MUTED, fontsize=10.5, fontweight="bold",
        ha="center", va="center", zorder=6)

ax.set_xlim(-0.45, 5.45)
ax.set_ylim(-0.029, 0.048)
ax.set_xticks(range(len(AGE_GROUPS)))
ax.set_xticklabels(AGE_GROUPS, fontsize=9)
ax.set_yticks([-0.02, 0, 0.02, 0.04])
ax.set_yticklabels(["-0.02", "0", "0.02", "0.04"])
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)
ax.grid(axis="x", visible=False)
ax.spines["bottom"].set_color("#b3b3b3")
ax.tick_params(axis="x", direction="in", length=3.5, color="#b3b3b3", pad=6)
x_axis_label(ax, "Age group", fontsize=9.5, labelpad=6)

finalize(
    ax,
    title="Female Uber drivers receive better tips than men",
    descriptor="Expected tip by Uber driver’s age and gender\nRelative to male drivers aged 21-25, $",
    source=(
        "Source: “Evidence from a Nationwide Tipping Field Experiment”\n"
        "by B. Chandar et al., National Bureau of Economic Research"
    ),
    y_axis_right=True,
    autoscale_y=False,
    footnote_lines=1,  # the source wraps to a second line
)
# finalize's bottom-spine recolour assumes the house dark spine; restore the
# reference's lighter axis line after the title stack is laid out.
ax.spines["bottom"].set_color("#b3b3b3")

out = Path(__file__).resolve().parent / "uber_tips.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Uber tips chart")
