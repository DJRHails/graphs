# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "scipy", "numpy"]
# ///
"""Replica of *The Economist*'s "World happiness rankings" bump chart.

Real data from the World Happiness Report 2025 (covering Gallup poll
years 2011–2024). The chart shows ranks across 2018–2024. The Nordic
core holds the head of the table in blues and greys; five
English-speaking countries — New Zealand, Australia, the US, Canada and
Britain — drift downward in reds, telling the chart's story. A faded
backdrop of non-highlighted countries provides context without
competing for attention. Right-edge labels give the final rank +
country name in the matching colour; the years repeat along the top
and bottom of the plot. A red annotation in the lower-right calls out
the trend.

Source CSV (community mirror of the WHR 2025 combined dataset):
``raw.githubusercontent.com/excainsights/HORIZON/main/Datasets/``
``World-Happiness_2011-2024_excaInsights_20251115.csv``

Columns: Year, Rank, Country name, Ladder score, ... — we use Rank
directly. Countries missing any of the 2018–2024 years are dropped so
each line has a value for every column (a ``bump_chart`` invariant).
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from examples._data import load_csv_text
from graphs import PALETTE, bump_chart, finalize, set_theme

set_theme()

DATA_URL = (
    "https://raw.githubusercontent.com/excainsights/HORIZON/main/Datasets/"
    "World-Happiness_2011-2024_excaInsights_20251115.csv"
)

years = list(range(2018, 2025))
year_labels = [str(years[0])] + [f"{y % 100:02d}" for y in years[1:]]

# Display names (shorter than the data's official names) for the chart.
DISPLAY_NAMES: dict[str, str] = {
    "United States": "US",
    "United Kingdom": "Britain",
}

# Parse the WHR CSV into ``country -> {year: rank}``.
raw_by_country: dict[str, dict[int, int]] = defaultdict(dict)
csv_text = load_csv_text(DATA_URL).lstrip("﻿")  # strip BOM if present
for row in csv.DictReader(csv_text.splitlines()):
    raw_by_country[row["Country name"]][int(row["Year"])] = int(row["Rank"])

# Keep only countries with coverage for every year we plot.
ranks: dict[str, list[int]] = {
    DISPLAY_NAMES.get(country, country): [by_year[y] for y in years]
    for country, by_year in raw_by_country.items()
    if all(y in by_year for y in years)
}

# Highlighted groups — names use the post-rename display form.
top_names = [
    "Finland", "Iceland", "Denmark", "Costa Rica", "Sweden",
    "Norway", "Netherlands", "Israel", "Luxembourg", "Switzerland",
]
eng_names = ["New Zealand", "Australia", "US", "Canada", "Britain"]
highlight = top_names + eng_names

missing = [n for n in highlight if n not in ranks]
if missing:
    raise RuntimeError(f"Highlight countries missing from data: {missing}")

# Force red for English-speaking countries; let the helper auto-pick for the
# top-10 (blues / greys).
colors_override: dict[str, str] = {name: PALETTE["red"] for name in eng_names}

fig, ax = plt.subplots(figsize=(7.5, 8.5))
# Bump chart needs explicit right-margin room for the rank labels (~20% of
# figure width) and a tall figure-relative bottom for tick labels on top
# and bottom; opt out of auto-layout so those margins stick.
fig.subplots_adjust(top=0.86, bottom=0.08, left=0.04, right=0.80)

bump_chart(
    ax,
    ranks,
    highlight=highlight,
    colors=colors_override,
    smoothing=0.5,
    x_labels=year_labels,
    x_labels_top=True,
    right_labels=True,
    right_label_fontsize=8.5,
    aspect=0.85,
    # The 2025 WHR revision has 135 fully-covered countries; without a rank
    # window the top-of-table story compresses into the top third.
    max_rank=40,
)

# Red annotation calling out the English-speaking trend.
ax.annotate(
    "English-speaking countries\nhave fallen down the rankings",
    xy=(5.0, 33),
    xycoords="data",
    color=PALETTE["red"],
    fontsize=9,
    fontweight="medium",
    ha="center",
    va="center",
    zorder=6,
)

finalize(
    ax,
    title="World happiness rankings",
    descriptor="",
    source="Source: [World Happiness Report 2025](https://worldhappiness.report/)",
    y_axis_right=False,
    title_x=0.04,
    auto_layout=False,
)

out = Path(__file__).resolve().parent / "bump_chart.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved bump chart")
