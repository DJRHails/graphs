# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy", "scipy"]
# ///
"""Redesign: was Britain right or wrong to vote Leave?

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few".
The original connected every individual poll point with a jagged line that
made opinion look erratic. The redesign:

* shows individual polls as scatter dots
* overlays a smoothed trend (Savitzky-Golay on a uniformly-spaced grid
  fitted by linear interpolation across time)
* leaves at least 33% of the plot area free below the lowest data point
  (Francis Gagnon's rule for broken y-axes)
* marks the broken baseline with the squiggle helper
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.signal import savgol_filter

from examples._data import load_csv_lines
from graphs import (
    PALETTE,
    broken_axis,
    finalize,
    inset_tick_labels,
    save_chart,
    scatter_standard,
    set_theme,
    year_axis,
)

set_theme()

URL = "http://infographics.economist.com/databank/Economist_brexit.csv"
dates, right, wrong = [], [], []
reader = csv.reader(load_csv_lines(URL))
for row in reader:
    if not row or len(row) < 3:
        continue
    try:
        d = datetime.strptime(row[0], "%d/%m/%y")
        r = float(row[1])
        w = float(row[2])
    except (ValueError, IndexError):
        continue
    dates.append(d)
    right.append(r)
    wrong.append(w)


def smooth(xs: list[datetime], ys: list[float], n: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Linear-interpolate to a uniform grid, then Savitzky-Golay smooth."""
    x_num = mdates.date2num(xs)
    grid = np.linspace(x_num[0], x_num[-1], n)
    y_interp = np.interp(grid, x_num, ys)
    y_smooth = savgol_filter(y_interp, window_length=31, polyorder=3)
    return grid, y_smooth


fig, ax = plt.subplots(figsize=(7, 4.4))

scatter_standard(ax, dates, right, color=PALETTE["blue"], size=12)
scatter_standard(ax, dates, wrong, color=PALETTE["red"], size=12)

xs_right, ys_right = smooth(dates, right)
xs_wrong, ys_wrong = smooth(dates, wrong)
ax.plot(xs_right, ys_right, color=PALETTE["blue"], linewidth=2.0)
ax.plot(xs_wrong, ys_wrong, color=PALETTE["red"], linewidth=2.0)

# ≥33% headroom below the lowest data point.
low = min(min(right), min(wrong))
high = max(max(right), max(wrong))
span = (high - low) / 0.62  # leave ~38% empty below the lowest dot
ax.set_ylim(low - (span - (high - low)), high + 1)

# Economist convention: full year for the leftmost tick, two-digit '%y for the rest.
# Anchor "2016" at the first data point (data begins mid-2016, so a Jan-1-2016
# tick would float in empty space); subsequent ticks sit on Jan 1 of each year.
_left = dates[0]
_year_ticks = [_left, datetime(2017, 1, 1), datetime(2018, 1, 1)]
ax.set_xlim(mdates.date2num(_left), ax.get_xlim()[1])
ax.set_xticks([mdates.date2num(d) for d in _year_ticks])
year_axis(ax, set_locator=False)
inset_tick_labels(ax, axis="x")

# Direct labels at the end of each line.
ax.text(xs_right[-1] + 8, ys_right[-1], "Right", color=PALETTE["blue"],
        va="center", ha="left", fontsize=9, fontweight="medium")
ax.text(xs_wrong[-1] + 8, ys_wrong[-1], "Wrong", color=PALETTE["red"],
        va="center", ha="left", fontsize=9, fontweight="medium")

broken_axis(ax, axis="both")

finalize(
    ax,
    title="Bremorse",
    descriptor='"In hindsight, do you think Britain was right or wrong to vote to leave the EU?"\n% responding',
    source="Source: [NatCen Social Research](https://natcen.ac.uk/)",
    autoscale_y=False,
)

save_chart(__file__)
