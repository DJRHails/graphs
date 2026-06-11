# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Estimated total Russian losses" chart.

Two synthetic series spanning Feb 24 2022 → May 14 2026:

* **Casualties** in dark slate — smoothed trend through ~36 individual
  estimates with a grey credible-range band, rising from 0 to ~1.3m.
* **Deaths** in red — same three-layer treatment, ~0.3m at the right
  edge.

Each series is rendered via ``smoothed_line`` so the eye reads scatter,
band, and trend as one. Direct in-chart labels replace the convention of
a swatch legend per series; an upper-left key explains the dot / band
glyphs once. A ``footnotes`` strip carries the meta-estimate caveat
above the multi-line source attribution.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.dates as mdates
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from graphs import (
    C_GRID,
    C_SPINE,
    PALETTE,
    finalize,
    footnotes,
    inset_tick_labels,
    save_chart,
    set_theme,
    smoothed_line,
    year_axis,
)

set_theme()

# Synthetic individual-estimate scatter across the war period.
np.random.seed(11)
start = datetime(2022, 2, 24)
end = datetime(2026, 5, 14)
start_num = mdates.date2num(start)
end_num = mdates.date2num(end)
n_points = 38
xs = np.linspace(start_num, end_num, n_points)
t = (xs - start_num) / (end_num - start_num)  # 0..1 within the period

# Casualties: convex growth from 0 → ~1.3m, scatter ±0.10m.
casualties_trend = 1.30 * (1 - np.exp(-2.8 * t))
y_casualties = casualties_trend + np.random.normal(0, 0.07, n_points)
y_casualties = np.clip(y_casualties, 0, None)

# Deaths: parallel curve from 0 → ~0.34m, scatter ±0.025m.
deaths_trend = 0.34 * (1 - np.exp(-2.4 * t))
y_deaths = deaths_trend + np.random.normal(0, 0.025, n_points)
y_deaths = np.clip(y_deaths, 0, None)

fig, ax = plt.subplots(figsize=(8, 4.8))

smoothed_line(
    ax, xs, y_casualties,
    color=C_SPINE, label="Casualties",
    window=7, band_alpha=0.18, scatter_alpha=0.35,
)
smoothed_line(
    ax, xs, y_deaths,
    color=PALETTE["red"], label="Deaths",
    window=7, band_alpha=0.18, scatter_alpha=0.35,
)

# Direct in-chart labels for each series (no legend swatch needed).
# Anchor near the top of each smoothed curve.
ax.annotate(
    "Casualties",
    xy=(mdates.date2num(datetime(2025, 1, 1)), 1.18),
    color=C_SPINE, fontsize=10, fontweight="bold",
    ha="center", va="bottom", zorder=6,
)
ax.annotate(
    "Deaths",
    xy=(mdates.date2num(datetime(2024, 10, 1)), 0.36),
    color=PALETTE["red"], fontsize=10, fontweight="bold",
    ha="center", va="bottom", zorder=6,
)

# Upper-left glyph key: dot for "Individual estimates", line+band for "Credible range".
glyph_dot = mlines.Line2D(
    [], [], color=C_SPINE, alpha=0.45,
    marker="o", linestyle="None", markersize=6,
    label="Individual estimates",
)


class _LineBandHandle:
    pass


class _LineBandHandler:
    """Legend handler: short line with a translucent band behind it.

    Kept private: bound to ``smoothed_line``'s line+band visual treatment
    and only used here. Promote to ``graphs/_legend.py`` if a second chart
    needs the same glyph in its legend.
    """

    def legend_artist(self, legend, orig_handle, fontsize, handlebox):
        x0, y0, w, h = (
            handlebox.xdescent,
            handlebox.ydescent,
            handlebox.width,
            handlebox.height,
        )
        band = mpatches.Rectangle(
            (x0, y0 - h * 0.10), w, h * 1.20,
            facecolor=C_SPINE, alpha=0.18, edgecolor="none",
            transform=handlebox.get_transform(),
        )
        line = mlines.Line2D(
            [x0, x0 + w], [y0 + h * 0.5, y0 + h * 0.5],
            color=C_SPINE, linewidth=1.8,
            transform=handlebox.get_transform(),
        )
        handlebox.add_artist(band)
        handlebox.add_artist(line)
        return band


legend = ax.legend(
    handles=[glyph_dot, _LineBandHandle()],
    labels=["Individual estimates", "Credible range"],
    handler_map={_LineBandHandle: _LineBandHandler()},
    loc="upper left",
    frameon=False,
    fontsize=8.5,
    handlelength=1.8,
    handletextpad=0.6,
    borderaxespad=0.4,
)
for txt in legend.get_texts():
    txt.set_color(C_SPINE)

# Axis cosmetics.
ax.set_xlim(start_num, end_num)
ax.set_ylim(0, 1.55)
year_ticks = [datetime(y, 1, 1) for y in (2022, 2023, 2024, 2025, 2026)]
ax.set_xticks([mdates.date2num(d) for d in year_ticks])
year_axis(ax, set_locator=False)
inset_tick_labels(ax, axis="x")
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)

finalize(
    ax,
    title="Estimated* total Russian losses",
    descriptor="Russia-Ukraine war, February 24th 2022 to May 14th 2026, m",
    source="",
    y_axis_right=True,
    autoscale_y=False,
    title_x=0.02,
    footnote_lines=4,  # meta-estimate note wraps + multi-line source
)
footnotes(
    fig,
    "*Meta-estimate based on trends in war intensity, territory shifts "
    "and credible open-source and intelligence assessments of losses",
    source=(
        "Sources: [DMSP Nighttime Lights](https://eogdata.mines.edu/products/dmsp/); "
        "[European Space Agency](https://www.esa.int/); "
        "[EUMETSAT](https://www.eumetsat.int/); "
        "[Institute for the Study of War](https://www.understandingwar.org/); "
        "[AEI's Critical Threats Project](https://www.criticalthreats.org/); "
        "[NASA](https://www.nasa.gov/); "
        "[WorldPop](https://www.worldpop.org/); "
        "[The Economist](https://www.economist.com/)"
    ),
)

save_chart(__file__)
