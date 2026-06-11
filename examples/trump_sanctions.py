# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: Donald Trump has imposed more financial sanctions than any other president.

The Economist daily chart (2019). Vertical bar time series of yearly additions
to the US specially designated nationals and blocked persons list, 2001-18,
with tinted presidential-era bands (Bush / Obama / Trump) behind the bars.
Values were read off the original chart against its 500-unit gridlines
(2017-18 match Gibson Dunn's reported totals of ~944 and ~1,474).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import (
    C_RED_DATA,
    C_SPINE,
    PALETTE,
    bar_v,
    finalize,
    highlight_panel,
    inset_tick_labels,
    set_theme,
)

set_theme()

years = list(range(2001, 2019))
additions = [
    350, 175, 590, 710, 320, 285, 450, 520,  # Bush, 2001-08
    285, 615, 490, 580, 545, 575, 420, 690,  # Obama, 2009-16
    945, 1470,                               # Trump, 2017-18
]

fig, ax = plt.subplots(figsize=(6.4, 5.0))

# Presidential-era bands — thin white gaps act as the era dividers.
# Band colour sampled from the original's pale-blue plot panel.
C_ERA_BAND = "#D7E8F0"
X_LO, X_HI = 2000.45, 2018.55
eras = [("Bush", X_LO, 2008.46), ("Obama", 2008.54, 2016.46), ("Trump", 2016.54, X_HI)]
for name, x0, x1 in eras:
    highlight_panel(ax, x0, x1, color=C_ERA_BAND)
    ax.text(
        (x0 + x1) / 2,
        0.955,
        name,
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=9,
        color=PALETTE["blue"],
    )

# Opt-in styleguide data red — the original's bars are the bright Economist red.
bar_v(ax, years, additions, color=C_RED_DATA, highlight_max=False, width=0.7)

ax.set_xlim(X_LO, X_HI)
# Headroom above the 1,500 gridline mirrors the original's era-label strip.
ax.set_ylim(0, 1940)
ax.set_yticks([0, 500, 1000, 1500])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))

ax.set_xticks([2001, 2005, 2010, 2015, 2018])
ax.set_xticklabels(["2001", "05", "10", "15", "18"])
# Original draws a small dark tick below the axis for every year (minor
# ticks coinciding with the labelled majors simply overdraw them).
ax.set_xticks(years, minor=True)
ax.tick_params(axis="x", which="both", length=3.5, color=C_SPINE)
inset_tick_labels(ax, axis="x")

finalize(
    ax,
    title="Donald Trump has imposed more financial sanctions than any other president",
    descriptor="United States, specially designated nationals and blocked persons list, number of additions",
    source="Source: Gibson, Dunn & Crutcher",
    autoscale_y=False,
)

out = Path(__file__).resolve().parent / "trump_sanctions.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Trump-sanctions chart")
