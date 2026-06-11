# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica: What is driving gold's relentless rally? (The Economist, 2026).

Indexed line chart (January 1st 2025 = 100) of returns on gold in dollar
terms versus the S&P 500, daily through early February 2026. Gold climbs
relentlessly to ~187 while the S&P 500 dips hard in April before grinding
back to ~114. Values are hand-traced anchors from the original chart with
daily interpolation plus small seeded noise for price-like texture.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.dates as mdates
import numpy as np

from graphs import (
    C_LABEL,
    C_RED,
    C_SPINE,
    finalize,
    index_marker,
    save_chart,
    set_theme,
    subplots,
)

set_theme()

C_SP500 = "#e9ada2"  # pale salmon sampled from the original

# Hand-traced anchors: (date, index value), January 1st 2025 = 100.
GOLD_ANCHORS = [
    (date(2025, 1, 1), 100.0),
    (date(2025, 1, 10), 101.5),
    (date(2025, 1, 31), 105.5),
    (date(2025, 2, 11), 110.5),
    (date(2025, 2, 24), 112.0),
    (date(2025, 2, 28), 108.5),
    (date(2025, 3, 10), 110.5),
    (date(2025, 3, 20), 115.0),
    (date(2025, 3, 31), 118.5),
    (date(2025, 4, 3), 117.0),
    (date(2025, 4, 11), 123.0),
    (date(2025, 4, 22), 127.0),
    (date(2025, 4, 30), 121.5),
    (date(2025, 5, 15), 119.0),
    (date(2025, 5, 30), 123.0),
    (date(2025, 6, 13), 126.0),
    (date(2025, 6, 30), 121.0),
    (date(2025, 7, 22), 123.5),
    (date(2025, 7, 31), 121.5),
    (date(2025, 8, 15), 124.5),
    (date(2025, 8, 31), 126.5),
    (date(2025, 9, 15), 133.0),
    (date(2025, 9, 30), 140.5),
    (date(2025, 10, 8), 148.0),
    (date(2025, 10, 20), 161.0),
    (date(2025, 10, 28), 147.0),
    (date(2025, 11, 6), 152.5),
    (date(2025, 11, 14), 150.0),
    (date(2025, 11, 25), 156.0),
    (date(2025, 12, 5), 157.5),
    (date(2025, 12, 16), 161.0),
    (date(2025, 12, 31), 166.0),
    (date(2026, 1, 9), 171.0),
    (date(2026, 1, 16), 177.0),
    (date(2026, 1, 22), 174.5),
    (date(2026, 1, 28), 180.0),
    (date(2026, 2, 5), 187.0),
]

SP500_ANCHORS = [
    (date(2025, 1, 1), 100.0),
    (date(2025, 1, 24), 103.0),
    (date(2025, 2, 19), 104.5),
    (date(2025, 2, 28), 101.0),
    (date(2025, 3, 13), 95.0),
    (date(2025, 3, 25), 97.5),
    (date(2025, 4, 2), 95.5),
    (date(2025, 4, 8), 85.0),
    (date(2025, 4, 24), 92.5),
    (date(2025, 5, 12), 99.0),
    (date(2025, 5, 30), 101.0),
    (date(2025, 6, 30), 104.5),
    (date(2025, 7, 31), 107.0),
    (date(2025, 8, 29), 109.0),
    (date(2025, 9, 30), 110.5),
    (date(2025, 10, 29), 112.5),
    (date(2025, 11, 20), 107.5),
    (date(2025, 12, 5), 111.5),
    (date(2025, 12, 26), 114.0),
    (date(2026, 1, 15), 114.5),
    (date(2026, 1, 26), 112.5),
    (date(2026, 2, 5), 114.0),
]


def _daily(anchors: list[tuple[date, float]], noise: float, seed: int):
    """Interpolate anchors to a daily series with small seeded noise."""
    xs = np.array([mdates.date2num(d) for d, _ in anchors])
    vals = np.array([v for _, v in anchors])
    days = np.arange(xs[0], xs[-1] + 1)
    wiggle = np.random.default_rng(seed).normal(0, noise, days.size)
    wiggle[0] = 0.0
    return days, np.interp(days, xs, vals) + wiggle


gold_x, gold_y = _daily(GOLD_ANCHORS, noise=0.7, seed=4)
sp_x, sp_y = _daily(SP500_ANCHORS, noise=0.5, seed=11)

fig, ax = subplots("daily", height=6.3)

ax.plot(sp_x, sp_y, color=C_SP500, linewidth=1.8, zorder=3)
ax.plot(gold_x, gold_y, color=C_RED, linewidth=1.8, zorder=4)

# Index baseline: black rule at 100 + black dot on the indexed point.
index_marker(ax, x=gold_x[0], y=100, rule_color=C_SPINE, dot_size=42)
ax.axhline(100, color=C_SPINE, linewidth=1.2, zorder=2)  # original's rule is heavier

# Direct labels (black, per the original).
ax.annotate(
    "Gold",
    xy=(mdates.date2num(date(2025, 9, 12)), 183),
    color=C_SPINE, fontsize=10, fontweight="bold", ha="center", va="bottom",
)
ax.annotate(
    "$ terms",
    xy=(mdates.date2num(date(2025, 9, 12)), 176),
    color=C_SPINE, fontsize=9.5, ha="center", va="bottom",
)
ax.annotate(
    "S&P 500",
    xy=(mdates.date2num(date(2025, 9, 20)), 119),
    color=C_SPINE, fontsize=9.5, ha="center", va="bottom",
)

# Axes: the bottom spine is the x-axis baseline; month-boundary tick
# marks hang from it, letter labels sit between them, year labels below.
month_starts = [date(2025, m, 1) for m in range(1, 13)] + [
    date(2026, 1, 1),
    date(2026, 2, 1),
]
ax.set_xticks([mdates.date2num(d) for d in month_starts])
ax.set_xticklabels([""] * len(month_starts))
month_mids = [date(2025, m, 16) for m in range(1, 13)] + [date(2026, 1, 16)]
ax.set_xticks([mdates.date2num(d) for d in month_mids], minor=True)
ax.set_xticklabels(list("JFMAMJJASOND") + ["J"], minor=True)
ax.tick_params(axis="x", which="minor", length=0, pad=8)
ax.tick_params(axis="x", which="major", length=6, color=C_LABEL)

for d, label in ((date(2025, 7, 1), "2025"), (date(2026, 1, 16), "2026")):
    ax.annotate(
        label,
        xy=(mdates.date2num(d), 0), xycoords=("data", "axes fraction"),
        xytext=(0, -24), textcoords="offset points",
        ha="center", va="top", fontsize=9, color=C_LABEL,
    )

ax.set_xlim(gold_x[0] - 5, gold_x[-1] + 3)
ax.set_ylim(80, 202)
ax.set_yticks(range(80, 201, 20))

# The spine doubles as the 80 line: drop the duplicate gridline before
# finalize so its on-grid "80" label continues the dark baseline instead.
ax.yaxis.get_gridlines()[0].set_visible(False)

finalize(
    ax,
    title="What is driving gold’s relentless rally?",
    descriptor="Returns, January 1st 2025=100",
    source="Source: LSEG Workspace",
    autoscale_y=False,
)

save_chart(__file__)
