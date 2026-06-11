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
goal.

The history is the real WHO estimated malaria case-incidence rate
(cases per 1,000 population at risk, expressed here as a %), pulled live
from the WHO Global Health Observatory indicator ``MALARIA_EST_INCIDENCE``
(global aggregate). The three forecast paths are scenario sketches: the
global-target path lands on the GTS 2016-30 milestone of a 90% cut in
incidence versus the 2015 baseline; the worst case drifts back toward the
2000-07 peak rate.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from examples._data import load_csv_text
from graphs import (
    PALETTE,
    finalize,
    footnotes,
    highlight_panel,
    inset_tick_labels,
    set_theme,
    y_labels_on_grid,
)

set_theme()

C_HISTORY = PALETTE["red"]
C_WORST = "#8e3a46"  # claret — worst-case scenario
C_EXPECTED = "#2da4bf"  # cyan — expected trend (and FORECAST tag)
C_TARGET = "#5cb8a7"  # pale teal — global target
C_BAND = "#d9e6f0"  # forecast panel tint

FORECAST_START = 2018
X_MAX = 2030

# WHO Global Health Observatory — global estimated malaria case incidence
# (cases per 1,000 population at risk). We plot it as a % of population at
# risk, i.e. the per-1,000 rate / 10, to match the original's axis.
_WHO_URL = (
    "https://ghoapi.azureedge.net/api/MALARIA_EST_INCIDENCE"
    "?$filter=SpatialDimType%20eq%20%27GLOBAL%27"
)
_who = json.loads(load_csv_text(_WHO_URL))["value"]
_rate = {row["TimeDim"]: row["NumericValue"] / 10.0 for row in _who}
years_hist = np.arange(2000, FORECAST_START + 1)
cases_hist = np.array([_rate[int(y)] for y in years_hist])

peak_rate = cases_hist[: 2007 - 2000 + 1].max()  # 2000-07 peak (footnote †)
target_2030 = round(0.10 * cases_hist[2015 - 2000], 2)  # GTS: 90% below 2015

# Forecast paths all leave the 2018 endpoint. The worst case drifts back up
# toward — but does not quite reach — the 2000-07 peak rate by 2030.
t = np.linspace(0.0, 1.0, 61)
years_fc = FORECAST_START + t * (X_MAX - FORECAST_START)
y0 = cases_hist[-1]
worst_2030 = y0 + 0.55 * (peak_rate - y0)
worst = y0 + (worst_2030 - y0) * t**1.2
expected = y0 - (y0 - 4.20) * t**0.9  # gentle drift down

# Global target: GTS 2016-30 — steep convex dive from the 2015 baseline to a
# 90% cut (the strategy's headline 2030 milestone).
t_tg = np.linspace(0.0, 1.0, 61)
years_tg = 2015 + t_tg * (X_MAX - 2015)
target = target_2030 + (cases_hist[2015 - 2000] - target_2030) * (1 - t_tg) ** 1.6

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
    color=C_EXPECTED, fontsize=9, fontweight="medium",
    ha="center", va="bottom", annotation_clip=False,
)

# Direct series labels, coloured to match their lines.
label_style = dict(fontsize=10, fontweight="medium", zorder=6)
ax.text(2000.3, 8.35, "Current estimates", color=C_HISTORY,
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
    source="Source: [WHO Global Health Observatory](https://www.who.int/data/gho)",
    max_width_frac=0.78,
)
y_labels_on_grid(ax)

out = Path(__file__).resolve().parent / "malaria.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved malaria chart")
