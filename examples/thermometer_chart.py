# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Thermometer (tick-and-dot) chart — ranked-category comparison.

Replicates the Economist styleguide "3 lines" thermometer variant using
Ben Schmidt's "horrible science" RateMyProfessors word-frequency study.
Data is made-up but shaped to suggest STEM disciplines use "horrible"
more often than humanities.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphs import cycle_for, finalize, save_chart, set_theme, subplots, thermometer, top_legend

set_theme()

categories = [
    "Mathematics",
    "Economics",
    "Computer Science",
    "Business",
    "Biology",
    "Philosophy",
    "English",
    "Psychology",
    "History",
    "Communication",
]

# Three series per category — illustrative values in 0–400 range.
# Shape: STEM/quantitative disciplines cluster higher; humanities lower.
values = [
    [305, 340, 380],  # Mathematics
    [260, 295, 330],  # Economics
    [230, 275, 310],  # Computer Science
    [195, 235, 270],  # Business
    [175, 210, 245],  # Biology
    [140, 175, 205],  # Philosophy
    [120, 150, 180],  # English
    [105, 130, 165],  # Psychology
    [85, 115, 140],   # History
    [60, 90, 115],    # Communication
]

fig, ax = subplots("wide", height=5.6)

thermometer(
    ax,
    categories,
    values,
    series_labels=["one", "two", "three"],
    colors_=cycle_for("thermometer"),
    dot=False,
)

ax.set_xlim(0, 400)
ax.set_xticks([0, 100, 200, 300, 400])
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_label_position("top")
ax.tick_params(axis="x", which="both", top=True, bottom=False, labeltop=True, labelbottom=False)

# Hands-off: tag the colour key BEFORE finalize so it reserves a band for it
# between the descriptor and the top-mounted x-ticks (0/100/200/300/400).
handles, labels = ax.get_legend_handles_labels()
top_legend(fig, handles, labels, ncol=3)

# finalize auto-layouts the wide left margin from the measured category names
# and pins the title stack above the top-mounted ticks.
finalize(
    ax,
    title="The horrible science",
    descriptor='Use of "Horrible" per million words\nin student reviews on RateMyProfessors.com*',
    source="Source: [Ben Schmidt](https://benschmidt.org/), Northeastern University",
    y_axis_right=False,
    title_x=0.02,
)

save_chart(__file__)
