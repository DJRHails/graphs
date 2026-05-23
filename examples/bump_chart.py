# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "scipy", "numpy"]
# ///
"""Replica of *The Economist*'s "World happiness rankings" bump chart.

Eight columns (2018–2025) of synthetic country ranks. The Nordic core
holds the top of the table in blues and greys; five English-speaking
countries — New Zealand, Australia, the US, Canada and Britain — drift
downward in reds, telling the chart's story. A faded backdrop of
non-highlighted countries provides context without competing for
attention. Right-edge labels give the final rank + country name in the
matching colour; the years repeat along the top and bottom of the
plot. A red annotation in the lower-right calls out the trend.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import PALETTE, bump_chart, finalize, set_theme

set_theme()

# Eight columns: 2018..2025. Highlighted ranks per country across years.
years = list(range(2018, 2026))
year_labels = [str(years[0])] + [f"{y % 100:02d}" for y in years[1:]]

# Top 10 — Nordic + small European nations that hold the head of the table.
# Synthetic but visually echoes the reference: a tight cluster swapping
# places, with Finland anchoring the top.
top_ranks: dict[str, list[int]] = {
    "Finland":      [1, 1, 1, 1, 1, 1, 1, 1],
    "Iceland":      [4, 4, 3, 3, 3, 2, 2, 2],
    "Denmark":      [2, 2, 2, 2, 2, 3, 3, 3],
    "Costa Rica":   [12, 11, 10, 9, 7, 6, 5, 4],
    "Sweden":       [3, 3, 5, 4, 5, 5, 6, 5],
    "Norway":       [5, 5, 4, 6, 6, 7, 7, 6],
    "Netherlands":  [6, 6, 6, 5, 4, 4, 4, 7],
    "Israel":       [10, 9, 9, 10, 8, 8, 9, 8],
    "Luxembourg":   [9, 10, 11, 8, 9, 9, 8, 9],
    "Switzerland":  [7, 7, 7, 7, 10, 10, 10, 10],
}

# English-speaking countries trending down in red.
# Australia and New Zealand cross in 2020 (Australia dips to 9 while NZ
# slides to 10) before NZ stabilises and Australia continues falling.
eng_ranks: dict[str, list[int]] = {
    "New Zealand":  [8, 8, 10, 11, 11, 11, 11, 11],
    "Australia":    [11, 10, 9, 11, 13, 14, 14, 15],
    "US":           [14, 15, 16, 17, 19, 21, 22, 23],
    "Canada":       [13, 14, 14, 15, 17, 19, 23, 25],
    "Britain":      [15, 16, 17, 18, 20, 22, 26, 29],
}

# Faded backdrop — a believable smear of mid-pack countries the eye treats
# as context. Synthetic but plausible: each line swirls between rank 12
# and rank 35 across the eight years.
backdrop_ranks: dict[str, list[int]] = {
    "Germany":      [16, 17, 17, 13, 14, 16, 17, 18],
    "Austria":      [17, 13, 12, 14, 15, 13, 13, 12],
    "Ireland":      [18, 18, 16, 16, 16, 17, 18, 17],
    "Belgium":      [19, 19, 18, 19, 18, 18, 16, 14],
    "Czech":        [20, 20, 20, 18, 12, 12, 12, 13],
    "Lithuania":    [21, 21, 22, 20, 21, 15, 15, 16],
    "France":       [22, 22, 24, 21, 22, 20, 19, 19],
    "Spain":        [23, 24, 28, 26, 27, 24, 25, 24],
    "Italy":        [24, 25, 30, 28, 30, 28, 27, 26],
    "Slovenia":     [25, 26, 27, 30, 24, 23, 21, 22],
    "Poland":       [26, 27, 26, 23, 26, 25, 28, 27],
    "Estonia":      [27, 28, 25, 22, 23, 26, 24, 20],
    "Singapore":    [28, 23, 21, 24, 25, 27, 30, 21],
    "Brazil":       [29, 29, 31, 29, 28, 30, 29, 28],
    "Mexico":       [30, 30, 23, 25, 29, 29, 31, 30],
    "UAE":          [31, 31, 32, 27, 31, 31, 32, 31],
    "Uruguay":      [32, 32, 33, 31, 32, 32, 33, 32],
    "Chile":        [33, 33, 34, 32, 33, 33, 34, 33],
    "Saudi Arabia": [34, 34, 35, 33, 34, 34, 35, 34],
    "Argentina":    [35, 35, 29, 34, 35, 35, 36, 35],
}

ranks: dict[str, list[int]] = {**top_ranks, **eng_ranks, **backdrop_ranks}
highlight = list(top_ranks) + list(eng_ranks)

# Force red for English-speaking countries; let the helper auto-pick for the
# top-10 (blues / greys).
colors_override: dict[str, str] = {name: PALETTE["red"] for name in eng_ranks}

fig, ax = plt.subplots(figsize=(7.5, 8.5))
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
)

# Red annotation calling out the English-speaking trend.
ax.annotate(
    "English-speaking countries\nhave fallen down the rankings",
    xy=(5.8, 33),
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
    source="Source: World Happiness Report 2026",
    y_axis_right=False,
    title_x=0.04,
)

out = Path(__file__).resolve().parent / "bump_chart.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved bump chart")
