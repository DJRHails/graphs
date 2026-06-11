# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Average wage relative to renters' wage — threshold lollipop replica.

Replicates The Economist's affordability chart for selected European
cities: each city's average wage as a multiple of the wage needed to
rent an average one-bedroom flat. Values below 1 are unaffordable
(red); values at or above 1 are affordable (slate).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.ticker import FixedLocator, NullLocator

from graphs import (
    finalize,
    footnotes,
    save_chart,
    set_theme,
    subplots,
    threshold_arrows,
    threshold_lollipop,
)

set_theme()

# Ranked ascending so Tbilisi sits at the top of the chart.
CITY_VALUES: list[tuple[str, float]] = [
    ("Tbilisi", 0.45),
    ("Prague", 0.50),
    ("Belgrade", 0.50),
    ("Budapest", 0.51),
    ("Lisbon", 0.52),
    ("Sofia", 0.55),
    ("Stockholm", 0.57),
    ("Riga", 0.63),
    ("London", 0.69),
    ("Dublin", 0.70),
    ("Madrid", 0.70),
    ("Athens", 0.71),
    ("Rome", 0.73),
    ("Oslo", 0.76),
    ("Warsaw", 0.85),
    ("Reykjavik", 0.85),
    ("Munich", 0.86),
    ("Paris", 0.87),
    ("Geneva", 0.88),
    ("Copenhagen", 0.93),
    ("Berlin", 1.00),
    ("Luxembourg", 1.06),
    ("Vienna", 1.07),
    ("Helsinki", 1.17),
    ("Brussels", 1.21),
    ("Bern", 1.22),
    ("Lyon", 1.32),
    ("Bonn", 1.36),
]

categories = [name for name, _ in CITY_VALUES]
values = [v for _, v in CITY_VALUES]

fig, ax = subplots("daily", height=5.9)

threshold_lollipop(ax, categories, values, threshold=1.0)

# Log x-axis with explicit tick stops matching the reference.
ax.set_xscale("log")
x_ticks = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
ax.set_xlim(0.38, 1.45)
ax.xaxis.set_major_locator(FixedLocator(x_ticks))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticklabels([f"{t:g}" for t in x_ticks])


finalize(
    ax,
    title="Average wage* relative to renters' wage†",
    descriptor="Selected European cities, 2025, log scale",
    source="",  # owned by footnotes() below so notes stack above it
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
    y_start=0.050,  # clear the top-mounted x-tick labels at the 4.6in width
    footnote_lines=2,
)

threshold_arrows(
    ax,
    threshold=1.0,
    left_text="Unaffordable",
    right_text="Affordable",
)

footnotes(
    fig,
    "*Based on location of workplace, not residence",
    "†30% of which is enough to pay rent on an average one-bedroom flat",
    source="Sources: [Eurostat](https://ec.europa.eu/eurostat); [ERI Economic Research Institute](https://www.erieri.com/); [The Economist](https://www.economist.com/)",
)

save_chart(__file__)
