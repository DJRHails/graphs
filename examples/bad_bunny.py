# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: how Americans feel about Bad Bunny at the Super Bowl.

The Economist daily chart (Feb 2026) — horizontal bars of YouGov survey
responses, % responding, x-axis on top. Values read off the original chart
(gridline spacing calibration): 34 / 28 / 27 / 11, summing to 100.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphs import bar_h, finalize, footnotes, save_chart, set_theme, subplots

set_theme()

# Listed top-to-bottom in the original; barh stacks bottom-up, so reverse.
categories = ["Don’t care", "Yes", "No", "Not sure"][::-1]
values = [34, 28, 27, 11][::-1]

FIG_H_IN = 6.0
fig, ax = subplots("daily", height=FIG_H_IN)

# Graph-design colour scheme rather than the original's flat brand red: the
# library's blue bars with the plurality ("Don't care") highlighted in C_RED.
bar_h(ax, categories, values)

# Bars fill ~72% of each slot (bar_h defaults to 60%).
for bar in ax.patches:
    bar.set_y(bar.get_y() - 0.06)
    bar.set_height(0.72)

ax.set_xlim(0, 35)
ax.set_xticks(range(0, 36, 5))

QUESTION = "Are you satisfied with Bad Bunny performing at half-time of this year’s Super Bowl?"

finalize(
    ax,
    title="How Americans feel about Bad Bunny at the Super Bowl",
    descriptor=QUESTION + "\nUnited States, % responding*",
    source="Source: YouGov/[The Economist](https://www.economist.com/)",
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
    y_start=0.025,  # breathing room above the title on this tall figure
)
# finalize auto-layouts the wide left margin from the measured ``bar_h`` category
# labels (which hang left of the axes), so they aren't clipped — no manual
# subplots_adjust needed.

# The survey question is the descriptor's semibold lead (the explicit "\n"
# before the units triggers it), so finalize bolds it automatically.

# Original stacks the date note one text line above the source line; the
# default packed layout would put it on the same row, right-aligned.
SOURCE_Y_OFFSET = 0.06  # finalize's source anchor below the axes
LINE_ADVANCE = 11.0 / 72.0 / FIG_H_IN  # one 9pt source line at 1.2 leading
note_y = ax.get_position().y0 - SOURCE_Y_OFFSET + LINE_ADVANCE
footnotes(fig, "*Jan 30th-Feb 2nd 2026", y=note_y)

save_chart(__file__)
