# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Redesign: dog weight vs. neck size.

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few".
The original cherry-picked y-axes so a 14% drop on one looked like a 7%
drop on the other — a fake perfect correlation. The redesign retains the
double scale but sizes both ranges so 1% of the midpoint occupies the same
vertical distance on each axis.
"""

import csv
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from examples._data import load_csv_lines
from graphs import PALETTE, color_axis, finalize, footnotes, get_font, save_chart, set_theme
from graphs._superscript import render_text_with_superscripts

set_theme()

URL = "http://infographics.economist.com/databank/Economist_dogs.csv"
years, weight, neck = [], [], []
reader = csv.reader(load_csv_lines(URL))
next(reader)
for row in reader:
    if not row or not row[0].isdigit():
        continue
    years.append(int(row[0]))
    weight.append(float(row[1]))
    neck.append(float(row[2]))

# Axis ranges: 1% of the midpoint occupies the same vertical pixel distance
# on both axes. Midpoints ≈ 19.3 kg and 43.4 cm → ratio 2.25, so neck range
# must be 2.25× the weight range.
fig, ax_left = plt.subplots(figsize=(7, 4.2))

ax_right = ax_left.twinx()

# Left axis carries neck size (cyan); right axis carries weight (red).
# Series-bound colours are preserved across the swap (neck=cyan, weight=red).
ax_left.plot(years, neck, color=PALETTE["cyan"], linewidth=2.0, label="Neck size (cm)")
ax_right.plot(years, weight, color=PALETTE["red"], linewidth=2.0, label="Weight (kg)")

# Aligned-tick ranges: 4 ticks on each axis at matching vertical fractions
# (0, 1/3, 2/3, 1) so gridlines coincide. Neck/weight range ratio is 2.0,
# slightly relaxed from the strict 2.25 proportional ideal in exchange for
# clean integer ticks and aligned gridlines.
ax_left.set_ylim(41.0, 47.0)
ax_right.set_ylim(18.0, 21.0)
ax_left.set_yticks([41, 43, 45, 47])
ax_right.set_yticks([18, 19, 20, 21])

# Only the tick labels (numbers) carry the series colour; the y-spines and
# tick marks are hidden so the horizontal gridlines (drawn from the left
# axis) carry value-reading on their own. The right (twin) axis hides its
# own gridlines so the left axis's gridlines — which line up vertically —
# read cleanly.
color_axis(ax_left, "left", PALETTE["cyan"], spine=False, ticks=False)
color_axis(ax_right, "right", PALETTE["red"], spine=False, ticks=False)
ax_left.spines["top"].set_visible(False)
ax_right.spines["top"].set_visible(False)
ax_right.grid(False)

ax_left.set_xticks(years[::2])


def _draw_axis_titles(fig, ax) -> None:
    """Place series labels at the top of each y-axis after finalize() runs.

    Deferred until after the title stack so we know where the descriptor
    block ends; the labels sit between the descriptor and the topmost tick.

    Kept private: this is the twin-axis variant (one label flush-left, one
    flush-right, no wrapping, IBM Plex Sans regular at 9pt). It differs
    enough from ``y_axis_label`` (single side, condensed font, wrap-aware)
    that merging the two would lose more clarity than it would gain.
    """
    fig.canvas.draw()
    bbox = ax.get_position()
    fp = fm.FontProperties(family=get_font(), weight="normal")
    render_text_with_superscripts(
        fig,
        bbox.x0,
        bbox.y1 + 0.005,
        "Neck size†, cm",
        fontsize=9,
        fontproperties=fp,
        color=PALETTE["cyan"],
        va="bottom",
        ha="left",
    )
    render_text_with_superscripts(
        fig,
        bbox.x1,
        bbox.y1 + 0.005,
        "Weight*, kg",
        fontsize=9,
        fontproperties=fp,
        color=PALETTE["red"],
        va="bottom",
        ha="right",
    )


# Pre-wrap the descriptor at ~70 chars so it lays out as two natural lines
# rather than a hard break. fig.text does not auto-wrap, so doing it here
# keeps rendering deterministic across DPIs.
_descriptor = textwrap.fill(
    "Characteristics of dogs registered with the UK's Kennel Club, "
    "average when fully grown",
    width=70,
)

finalize(
    ax_left,
    title="Fit as a butcher's dog",
    descriptor=_descriptor,
    source="",  # owned by footnotes() below so notes can pack alongside it
    y_axis_right=False,
    title_x=0.02,
    y_start=0.035,
    autoscale_y=False,
    footnote_lines=1,  # notes pack alongside source line
)

_draw_axis_titles(fig, ax_left)

footnotes(
    fig,
    "*Where at least 50 are registered per year",
    "†Where at least 100 are registered per year",
    source="Sources: [Kennel Club](https://www.thekennelclub.org.uk/); [The Economist](https://www.economist.com/)",
)

save_chart(__file__)
