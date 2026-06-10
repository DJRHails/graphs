# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: The Economist's variable-width (Mekko) bar chart of CO2 emissions.

Bar height is CO2 emissions per person (tonnes, 2017); bar width is
population (bn), so bar area is each region's total emissions — the
number printed on every bar, in gigatonnes. A dashed reference line
marks the global average. Values approximated from the published chart.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import finalize, footnotes, set_theme

set_theme()

C_AVG = "#5E9CAE"  # global-average dashed line + label
C_DARK = "#1A1A1A"  # in-bar labels on light fills

# (name, population bn, tonnes CO2 per person, fill) — heights/widths measured
# off the original; printed numbers are each region's total emissions, Gt.
REGIONS = [
    ("United States", 0.33, 17.6, "#A8172A"),
    ("Middle East", 0.23, 9.6, "#EE3740"),
    ("Europe", 0.82, 7.9, "#F16972"),
    ("China", 1.42, 7.5, "#F39CA1"),
    ("Americas", 0.66, 3.9, "#F8C1C1"),
    ("Asia Pacific", 1.45, 3.7, "#80CCC5"),
    ("India", 1.32, 1.85, "#00A1C1"),
    ("Africa", 1.27, 1.25, "#046C9E"),
]
GLOBAL_AVG = 4.6
X_MAX = 7.6

fig, ax = plt.subplots(figsize=(5.2, 5.5))

lefts = []
edge = 0.0
for _, pop, _, _ in REGIONS:
    lefts.append(edge)
    edge += pop

ax.bar(
    lefts,
    [pc for _, _, pc, _ in REGIONS],
    width=[pop for _, pop, _, _ in REGIONS],
    color=[c for _, _, _, c in REGIONS],
    align="edge",
    linewidth=0,
    zorder=2,
)

# Global-average reference line: dashes start above the Asia Pacific bar.
ax.plot([4.15, X_MAX], [GLOBAL_AVG, GLOBAL_AVG], color=C_AVG, linewidth=1.0,
        linestyle=(0, (4, 2)), zorder=3)
ax.text(6.5, GLOBAL_AVG + 0.55, "Global average ", color=C_AVG, fontsize=9.5,
        ha="right", va="baseline", fontweight="bold")
ax.text(6.5, GLOBAL_AVG + 0.55, "4.6", color=C_AVG, fontsize=9.5,
        ha="left", va="baseline")


def bar_label(x, y, name, value, color, *, ha="center", stacked=True):
    """Bold region name with its total-emissions value, stacked or inline."""
    if stacked:
        ax.text(x, y, name, color=color, fontsize=9.5, ha=ha, va="baseline",
                fontweight="bold", zorder=4)
        ax.text(x, y - 1.1, value, color=color, fontsize=9.5, ha=ha,
                va="baseline", zorder=4)
    else:
        ax.text(x, y, f"{name} ", color=color, fontsize=9.5, ha="right",
                va="baseline", fontweight="bold", zorder=4)
        ax.text(x, y, value, color=color, fontsize=9.5, ha="left",
                va="baseline", zorder=4)


# United States — label to the right of the bar top, with the total spelt out.
ax.text(0.40, 16.6, "United States", color="#A8172A", fontsize=9.5,
        ha="left", va="baseline", fontweight="bold")
ax.text(0.40, 15.5, "Total emissions 5.3 gigatonnes", color="#A8172A",
        fontsize=9.5, ha="left", va="baseline")

# Middle East — label just above its bar top, hanging to the right.
bar_label(1.68, 9.85, "Middle East", "2.7", "#C63C4D", stacked=False)

# Europe, China, Asia Pacific — dark stacked labels inside the bars.
bar_label(lefts[2] + 0.41, 4.1, "Europe", "4.9", C_DARK)
bar_label(lefts[3] + 0.71, 4.1, "China", "9.8", C_DARK)
bar_label(lefts[5] + 0.725, 2.4, "Asia Pacific", "5.1", C_DARK)

# Americas — pale pink label floating above its bar, at the average line.
bar_label(lefts[4] + 0.94, 4.35, "Americas", "2.4", "#F29CA3",
          stacked=False)

# India, Africa — white inline labels inside the blue bars.
bar_label(lefts[6] + 0.78, 1.25, "India", "2.5", "white", stacked=False)
bar_label(lefts[7] + 0.80, 0.45, "Africa", "1.3", "white", stacked=False)

ax.set_xlim(0, X_MAX)
ax.set_ylim(0, 18)
ax.set_yticks(range(0, 19, 3))
ax.set_xticks(range(0, 8))
ax.set_xlabel("Population, 2017, bn")

finalize(
    ax,
    title="America is the biggest polluter of CO₂ per person",
    marker="rule",
    descriptor="CO₂ emissions per person, 2017, tonnes",
    autoscale_y=False,
    footnote_lines=2,  # x-axis label sits between the ticks and the source
)
footnotes(fig, source="Sources: GCP; CDIAC; UN")

out = Path(__file__).resolve().parent / "co2_emissions.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved CO2-emissions chart")
