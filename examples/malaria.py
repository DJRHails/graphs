# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "How the world is doing in the battle
against Malaria" daily chart.

One solid red history line (cases as a % of the population at risk,
2000-18) splits at 2018 into three dashed forecast paths inside a pale
blue FORECAST band: a claret worst-case scenario climbing back towards
its 2000-07 peak rate, a cyan expected trend drifting down, and a teal
global target diving towards the WHO Global Technical Strategy's 2030
goal. Data are synthesized to match the published shape.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from graphs import (
    PALETTE,
    finalize,
    footnotes,
    highlight_panel,
    inset_tick_labels,
    set_theme,
)

set_theme()

C_HISTORY = PALETTE["red"]
C_WORST = "#8e3a46"  # claret — worst-case scenario
C_EXPECTED = "#2da4bf"  # cyan — expected trend (and FORECAST tag)
C_TARGET = "#5cb8a7"  # pale teal — global target
C_BAND = "#d9e6f0"  # forecast panel tint

FORECAST_START = 2018
X_MAX = 2030

# History 2000-18: noisy decline from ~7.1 to a ~5.7 trough, small uptick.
years_hist = np.arange(2000, FORECAST_START + 1)
cases_hist = np.array(
    [7.10, 7.00, 6.85, 6.95, 6.85, 6.80, 6.60, 6.65, 6.75,
     6.70, 6.50, 6.30, 6.15, 6.00, 5.85, 5.72, 5.68, 5.80, 5.88]
)

# Forecast paths all leave the 2018 endpoint.
t = np.linspace(0.0, 1.0, 61)
years_fc = FORECAST_START + t * (X_MAX - FORECAST_START)
y0 = cases_hist[-1]
worst = y0 + (6.90 - y0) * t**1.15  # back towards the 2000-07 peak rate
expected = y0 - (y0 - 4.40) * t**0.9  # gentle drift down

# Global target: GTS 2016-30 — steep convex dive from the 2016 level to ~0.35.
t_tg = np.linspace(0.0, 1.0, 61)
years_tg = 2016 + t_tg * (X_MAX - 2016)
target = 0.35 + (cases_hist[16] - 0.35) * (1 - t_tg) ** 1.6

fig, ax = plt.subplots(figsize=(5.2, 5.6))

highlight_panel(ax, FORECAST_START, X_MAX, color=C_BAND)

ax.plot(years_hist, cases_hist, color=C_HISTORY, linewidth=2.2, zorder=4)
dash = dict(linewidth=1.7, dashes=(3, 2), zorder=3)
ax.plot(years_fc, worst, color=C_WORST, **dash)
ax.plot(years_fc, expected, color=C_EXPECTED, **dash)
ax.plot(years_tg, target, color=C_TARGET, **dash)

# FORECAST header: teal rule across the band top, tag above it.
ax.plot(
    [FORECAST_START, X_MAX], [9.0, 9.0],
    color=C_EXPECTED, linewidth=1.4, clip_on=False, zorder=5,
)
ax.annotate(
    "FORECAST",
    xy=((FORECAST_START + X_MAX) / 2, 9.0),
    xytext=(0, 4), textcoords="offset points",
    color=C_EXPECTED, fontsize=8.5, fontweight="medium",
    ha="center", va="bottom", annotation_clip=False,
)

# Direct series labels, coloured to match their lines.
label_style = dict(fontsize=9, fontweight="medium", zorder=6)
ax.text(2000.3, 7.55, "Current estimates", color=C_HISTORY,
        ha="left", va="bottom", **label_style)
ax.text(2024.6, 7.10, "Worst-case\nscenario†", color=C_WORST,
        ha="center", va="bottom", linespacing=1.25, **label_style)
ax.text(2029.6, 4.95, "Expected\ntrend", color=C_EXPECTED,
        ha="right", va="bottom", linespacing=1.25, **label_style)
ax.text(2015.2, 4.65, "Global target*", color=C_TARGET,
        ha="right", va="top", **label_style)

ax.set_xlim(2000, X_MAX)
ax.set_ylim(0, 9)
ax.set_xticks(np.arange(2000, X_MAX + 1, 5))
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, _pos: f"{x:.0f}" if x == 2000 else f"{x % 100:02.0f}")
)
inset_tick_labels(ax, axis="x")
ax.set_yticks([0, 3, 6, 9])

finalize(
    ax,
    title="How the world is doing in the battle against Malaria",
    marker="rule",
    descriptor="Malaria, cases as a % of population at risk",
    source="",
    y_axis_right=True,
    autoscale_y=False,
    footnote_lines=2,
)
# Small max_width_frac forces the stacked footer: notes on their own
# left-aligned row above the source line, matching the original.
footnotes(
    fig,
    "*Global Technical Strategy for Malaria 2016-30",
    "†At peak rate, 2000-07",
    source="Source: [WHO](https://www.who.int/)",
    max_width_frac=0.78,
)

out = Path(__file__).resolve().parent / "malaria.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved malaria chart")
