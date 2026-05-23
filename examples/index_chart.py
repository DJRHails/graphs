# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Index chart — index_marker baseline, highlight_panel event band,
secondary highlight_label, and broken_axis for the non-zero baseline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from graphs import (
    broken_axis,
    finalize,
    highlight_label,
    highlight_panel,
    index_marker,
    label_lines,
    set_theme,
)

set_theme()

years = np.arange(2010, 2026)
# Two indexed series, both pinned to 100 at 2015
us = np.array(
    [88, 92, 95, 97, 99, 100, 102, 104, 107, 110, 95, 108, 114, 118, 122, 125]
)
eu = np.array([90, 92, 94, 96, 98, 100, 101, 103, 104, 105, 92, 99, 103, 105, 107, 109])

fig, ax = plt.subplots(figsize=(7.2, 4.6))

# Pandemic shock band — main message of the chart, but the styleguide
# reserves red emphasis; for web use the subtle tint instead.
highlight_panel(ax, 2019.0, 2021.0, label="Pandemic")

(line_us,) = ax.plot(years, us, label="United States")
(line_eu,) = ax.plot(years, eu, label="EU")

# Index baseline + red rule at the index value
index_marker(ax, x=2015, y=100)

# Secondary callout — FORECAST styling for the last two years
highlight_label(ax, xy=(2024, eu[-1] + 2), text="Forecast", role="secondary")

# Non-zero baseline signal (y-axis starts well above 0)
ax.set_ylim(85, 130)
broken_axis(ax)

label_lines(ax)

finalize(
    ax,
    title="The US pulls ahead",
    descriptor="Real GDP, index, 2015 = 100",
    source="Source: IMF; World Bank",
)

out = Path(__file__).resolve().parent / "index_chart.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved index chart")
