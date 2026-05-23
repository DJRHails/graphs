# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Redesign: US trade deficit vs. manufacturing employment.

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few".
The original forced a positive-and-negative double-axis with two different
baselines (one at the top of the chart, one at the bottom). The redesign
splits the two series into stacked panels — each on its own honest scale.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from examples._data import load_csv_lines
from graphs import PALETTE, finalize, footnotes, inset_tick_labels, panel_label, right_axis, set_theme

set_theme()

URL = "http://infographics.economist.com/databank/Economist_us-trade-manufacturing.csv"
years, deficit, manuf = [], [], []
reader = csv.reader(load_csv_lines(URL))
next(reader)
for row in reader:
    if not row or not row[0].isdigit():
        continue
    years.append(int(row[0]))
    deficit.append(float(row[1]))
    manuf.append(float(row[2]))

fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(7, 5.4), sharex=True)
fig.subplots_adjust(top=0.82, bottom=0.08, left=0.02, right=0.98, hspace=0.28)

ax_top.fill_between(years, deficit, 0, color=PALETTE["red"], alpha=0.85, linewidth=0)
ax_bottom.plot(years, manuf, color=PALETTE["blue"], linewidth=2.0)

ax_top.set_ylim(-400, 0)
ax_bottom.set_ylim(11, 18)

panel_label(ax_top, "Trade deficit with China, $bn")
panel_label(ax_bottom, "Manufacturing employment, m")

for axis in (ax_top, ax_bottom):
    right_axis(axis)

ax_top.set_xlim(years[0], years[-1])
ax_bottom.set_xlim(years[0], years[-1])
ax_bottom.set_xticks(list(range(1995, 2017, 3)))
inset_tick_labels(ax_bottom, axis="x")

# Title stack on the top axes; source line drawn manually below the bottom.
finalize(
    ax_top,
    title="Free markets and free workers",
    descriptor="United States",
    source="",
    title_x=0.02,
    y_start=0.060,
    autoscale_y=False,
    auto_layout=False,  # stacked panels need explicit hspace
)
footnotes(fig, source="Sources: US Census Bureau; BLS")

out = Path(__file__).resolve().parent / "us_trade.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved US-trade chart")
