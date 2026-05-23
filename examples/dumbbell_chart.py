# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Dumbbell chart — The Economist style."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from graphs import dumbbell, finalize, set_theme, top_legend

set_theme()

countries = [
    "United States",
    "China",
    "Germany",
    "Japan",
    "India",
    "Brazil",
]
gdp_2000 = [10.25, 1.21, 1.95, 4.72, 0.47, 0.65]
gdp_2020 = [20.93, 14.72, 3.84, 5.06, 2.62, 1.44]

fig, ax = plt.subplots(figsize=(8, 4.5))

dumbbell(
    ax,
    countries,
    gdp_2000,
    gdp_2020,
    label_start="2000",
    label_end="2020",
)
ax.set_xlim(-0.5, 24)
ax.xaxis.set_major_formatter(
    ticker.FuncFormatter(lambda v, _: f"${v:.0f}tn")
)

finalize(
    ax,
    title="The great divergence",
    descriptor="GDP in current US dollars, selected economies",
    source="Source: [World Bank](https://www.worldbank.org/)",
    y_axis_right=False,
    title_x=0.02,
)

bbox = ax.get_position()
top_legend(
    fig,
    ax._dumbbell_handles,
    ["2000", "2020"],
    x=bbox.x1,
    align="right",
    fontsize=8.5,
    ncol=2,
)

out = Path(__file__).resolve().parent / "dumbbell_chart.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved dumbbell chart")
