# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Horizontal bar chart — The Economist style."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import bar_h, finalize, set_theme

set_theme()

categories = ["Germany", "France", "Italy", "Spain", "Poland", "Sweden"]
values = [3.7, 2.4, 1.8, 2.1, 4.2, 3.1]

fig, ax = plt.subplots(figsize=(7, 4))

bar_h(ax, categories, values)

finalize(
    ax,
    title="Eastern promise",
    descriptor="GDP growth rate, %, 2023",
    source="Source: [Eurostat](https://ec.europa.eu/eurostat)",
    y_axis_right=False,
    title_x=0.02,
)

out = Path(__file__).resolve().parent / "bar_chart.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved bar chart")
