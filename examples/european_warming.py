# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "The Great European Bake Off" chart.

Decadal mean temperature anomalies by continent, relative to the
1991-2020 baseline. The story is the divergence: Europe (red) starts near
the bottom of the pack in the 1950s but warms faster than anywhere else,
ending clearly above every other continent and well above the global mean
(dark grey). The remaining continents form a faded grey backdrop that
fans out from a cold mid-century, narrows through the baseline period, and
fans out again — warmer — by the 2010s.

Real data, from Berkeley Earth. Each continent is the regional land-only
TAVG series; "World" is the global land-and-ocean series. Monthly
anomalies were averaged to annual, re-baselined to each series' own
1991-2020 mean, then averaged over each non-overlapping decade ending in
the labelled year (e.g. "1990" = the mean of 1981-1990). The continental
land product runs to 2020, so every series — World included — uses the
same decade windows through 2011-2020 to keep the comparison honest;
the published Economist chart uses Copernicus ERA5 to 2025 and so ends
hotter. Antarctica's land coverage only becomes usable from the 1960s,
so its line starts mid-chart. Values below are the computed decadal
means (°C).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.patheffects as pe
import numpy as np

from graphs import (
    C_GRID,
    C_RED,
    finalize,
    footnotes,
    save_chart,
    set_theme,
    subplots,
    x_axis_label,
)

set_theme()

NaN = np.nan

# Decade ending on the x-axis; anomalies in °C vs each series' 1991-2020 mean.
YEARS = [1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020]

europe = [-0.95, -1.03, -1.17, -1.08, -0.78, -0.42, -0.06, 0.48]
world = [-0.62, -0.62, -0.65, -0.55, -0.35, -0.21, 0.01, 0.20]

# Other continents — the de-emphasised grey backdrop, every line below
# Europe's endpoint. Antarctica's pre-1960s land coverage is too sparse to
# report, so it starts at the 1970 decade.
backdrop = {
    "Asia": [-1.04, -1.13, -1.07, -0.99, -0.69, -0.44, 0.04, 0.40],
    "Africa": [-0.83, -0.89, -0.87, -0.80, -0.46, -0.29, 0.11, 0.19],
    "North America": [-0.76, -0.75, -0.98, -0.99, -0.67, -0.34, 0.09, 0.25],
    "South America": [-0.81, -0.79, -0.61, -0.62, -0.40, -0.21, -0.03, 0.25],
    "Oceania": [-0.99, -0.82, -0.70, -0.57, -0.33, -0.24, 0.00, 0.24],
    "Antarctica": [NaN, NaN, -0.77, -0.42, -0.28, -0.21, 0.09, 0.12],
}

C_BACKDROP = "#c6c6c1"  # warm light grey, well behind the data
C_WORLD = "#656566"  # medium grey, the global-mean reference line

fig, ax = subplots("daily", height=4.4)


def halo(linewidth, extra=2.2):
    """White outline behind a line so crossings read cleanly (as bump_chart).

    Only the two highlighted lines get one — the faded backdrop reads as a
    single mass, so haloing it would just carve distracting white gaps.
    """
    return [pe.withStroke(linewidth=linewidth + extra, foreground="white")]


for series in backdrop.values():
    ax.plot(YEARS, series, color=C_BACKDROP, linewidth=1.6, zorder=2,
            solid_capstyle="round", solid_joinstyle="round")

ax.plot(YEARS, world, color=C_WORLD, linewidth=2.6, zorder=4,
        solid_capstyle="round", solid_joinstyle="round",
        path_effects=halo(2.6))
ax.plot(YEARS, europe, color=C_RED, linewidth=2.9, zorder=5,
        solid_capstyle="round", solid_joinstyle="round",
        path_effects=halo(2.9))

# Direct labels sit on the two highlighted lines.
ax.text(2006, 0.18, "Europe", color=C_RED, fontsize=11,
        fontweight="bold", ha="center", va="bottom", zorder=6)
ax.text(1968, -0.42, "World", color=C_WORLD, fontsize=11,
        fontweight="bold", ha="center", va="bottom", zorder=6)

ax.set_xlim(1946, 2024)
ax.set_ylim(-1.32, 0.62)
ax.set_xticks(YEARS)
ax.set_xticklabels(["1950", "60", "70", "80", "90", "2000", "10", "20"])
ax.set_yticks([0.5, 0.0, -0.5, -1.0])
ax.set_yticklabels(["0.5", "0", "-0.5", "-1.0"])
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)
ax.tick_params(axis="x", length=4, pad=4)

x_axis_label(ax, "Decade ending")

finalize(
    ax,
    title="The Great European Bake Off",
    descriptor=(
        "Average temperature anomalies by continent\n"
        "Relative to the 1991-2020 average, °C"
    ),
    source="",
    autoscale_y=False,
    footnote_lines=1,
)
# finalize() draws the dark zero centreline (the y-range straddles 0) and
# extends the bottom baseline to meet the on-grid gridlines automatically.

footnotes(
    fig,
    "Continents: land surface only. World: land and ocean.",
    source="Source: [Berkeley Earth](https://berkeleyearth.org/data/)",
)

save_chart(__file__)
