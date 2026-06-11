# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Millennials spend more time than past
generations with their children" daily chart.

Minutes per day US mothers spend on child care, by the mother's age, one
line per generation. Generations are chronological snapshots of the same
metric, so colours follow the ``graphs.snapshot_palette`` ramp — but the
two grey cohorts are pinned to values sampled from the published chart,
which uses warm greys (Silent ``#63615b``, Baby-boomer ``#c0bfb6``)
rather than the library's slate tones. Values are read off the published
chart.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from graphs import (
    C_GRID,
    C_LABEL,
    finalize,
    footnotes,
    set_theme,
    snapshot_palette,
    y_labels_on_grid,
)

set_theme()

# Mother's age (5-year bins) → minutes per day, oldest generation first.
series = [
    ("Silent", [30, 35, 40, 45, 50, 55, 60], [67, 39, 28, 29, 38, 10, 21]),
    ("Baby-boomer", [20, 25, 30, 35, 40, 45, 50, 55, 60], [93, 90, 94, 77, 80, 61, 45, 42, 41]),
    ("Gen X", [20, 25, 30, 35, 40, 45, 50], [129, 133, 135, 116, 89, 68, 28]),
    ("Millennial", [20, 25, 30, 35], [132, 143, 162, 140]),
]
colors = dict(zip([name for name, _, _ in series], snapshot_palette(len(series))))
# The published chart's greys are warm, not slate — pin to sampled values.
colors["Silent"] = "#63615b"
colors["Baby-boomer"] = "#c0bfb6"

fig, ax = plt.subplots(figsize=(4.0, 5.2))

for name, ages, minutes in series:
    is_accent = name == "Millennial"
    ax.plot(
        ages,
        minutes,
        color=colors[name],
        linewidth=2.2 if is_accent else 1.8,
        marker="o",
        markersize=4.4 if is_accent else 3.8,
        zorder=5 if is_accent else 4,
    )

ax.set_xlim(19.3, 66.5)
ax.set_ylim(0, 172)
ax.set_xticks([20, 30, 40, 50, 60])
ax.set_xticks([25, 35, 45, 55], minor=True)
ax.set_yticks([0, 40, 80, 120, 160])
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)
ax.tick_params(axis="x", length=4, pad=4)
ax.tick_params(axis="x", which="minor", length=2.5)
ax.set_xlabel("Mother’s age", fontsize=9.5, fontweight="bold", color=C_LABEL, labelpad=6)

# Panel heading, top-left above the plot (the original pairs this chart
# with a "Fathers" panel).
ax.text(
    0.0, 1.04, "Mothers",
    transform=ax.transAxes, fontsize=10.5, fontweight="bold",
    color=C_LABEL, ha="left", va="bottom", zorder=6,
)

# Direct in-chart series labels, near-black like the reference (the line
# colour alone separates the cohorts; the labels stay readable).
_labels = [
    ("Millennial", 36.3, 135, "bold"),
    ("Gen X", 36.3, 114, "normal"),
    ("Baby-\nboomer", 53.5, 60, "normal"),
    ("Silent", 35.3, 15, "normal"),
]
for text, lx, ly, weight in _labels:
    ax.text(
        lx, ly, text,
        color=C_LABEL, fontsize=9.5, fontweight=weight,
        ha="left", va="center", linespacing=1.15, zorder=6,
    )

finalize(
    ax,
    title="Millennials spend more time than past generations with their children",
    descriptor="US parents*, minutes per day spent on child care†\nBy generation, 1975-2018",
    source="",
    y_axis_right=True,
    y_start=0.085,  # leave room for the "Mothers" panel heading
    autoscale_y=False,
    footnote_lines=3,
)
y_labels_on_grid(ax)
# Narrow figure: widen the right margin so the right-hand y-tick labels fit.
fig.subplots_adjust(right=0.915)
footnotes(
    fig,
    "*Who live with partner and at least one child under 18",
    "†Controlling for children under five",
    source="Source: American Heritage Time Use Study",
)

out = Path(__file__).resolve().parent / "millennial_parents.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved millennial parents chart")
