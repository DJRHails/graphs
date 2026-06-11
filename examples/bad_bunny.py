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

import matplotlib.pyplot as plt

from graphs import bar_h, finalize, footnotes, set_theme

set_theme()

# The original's bars use the Economist's bright digital red (sampled),
# not the library's deeper brand red.
BAR_RED = "#f5423c"

# Listed top-to-bottom in the original; barh stacks bottom-up, so reverse.
categories = ["Don’t care", "Yes", "No", "Not sure"][::-1]
values = [34, 28, 27, 11][::-1]

FIG_H_IN = 4.9
fig, ax = plt.subplots(figsize=(3.4, FIG_H_IN))
# Manual margins: auto-layout's left edge would clip the category labels
# (bar_h hangs them left of the axes), and the top-mounted x-ticks need
# extra headroom under the title stack.
fig.subplots_adjust(top=0.725, bottom=0.15, left=0.27, right=0.96)

bar_h(ax, categories, values, color=BAR_RED, highlight_max=False)

# Original's bars fill ~72% of each slot (bar_h defaults to 60%).
for bar in ax.patches:
    bar.set_y(bar.get_y() - 0.06)
    bar.set_height(0.72)

ax.set_xlim(0, 35)
ax.set_xticks(range(0, 36, 5))

QUESTION_LINES = (
    "Are you satisfied with Bad Bunny performing",
    "at half-time of this year’s Super Bowl?",
)

finalize(
    ax,
    title="How Americans feel about Bad Bunny at the Super Bowl",
    descriptor="\n".join(QUESTION_LINES) + "\nUnited States, % responding*",
    source="Source: YouGov/[The Economist](https://www.economist.com/)",
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
    auto_layout=False,
)

# The original sets the survey question in bold; finalize renders the
# descriptor in one weight, so bold those two lines after the fact.
for text in fig.texts:
    if text.get_text() in QUESTION_LINES:
        text.set_fontweight("bold")

# Original stacks the date note one text line above the source line; the
# default packed layout would put it on the same row, right-aligned.
SOURCE_Y_OFFSET = 0.06  # finalize's source anchor below the axes
LINE_ADVANCE = 11.0 / 72.0 / FIG_H_IN  # one 9pt source line at 1.2 leading
note_y = ax.get_position().y0 - SOURCE_Y_OFFSET + LINE_ADVANCE
footnotes(fig, "*Jan 30th-Feb 2nd 2026", y=note_y)

out = Path(__file__).resolve().parent / "bad_bunny.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Bad Bunny chart")
