# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Redesign: Facebook likes for the British political left.

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few"
(The Economist, 2019). Fixes the original's truncated scale by showing
Mr Corbyn's bar in its entirety, and drops the three-shade orange hack.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt

from examples._data import load_csv_lines
from graphs import bar_h, finalize, set_theme, style_labels

set_theme()

URL = "http://infographics.economist.com/databank/Economist_corbyn.csv"
reader = csv.reader(load_csv_lines(URL))
next(reader)
rows = []
for row in reader:
    if not row or not row[0] or not row[1].strip() or row[0].startswith("Source"):
        continue
    rows.append((row[0].strip(), float(row[1])))

# Order ascending so Corbyn lands at the top of the chart.
rows.sort(key=lambda r: r[1])
labels = [r[0] for r in rows]
values = [r[1] for r in rows]

fig, ax = plt.subplots(figsize=(7, 3.6))

bar_h(ax, labels, [v / 1000 for v in values], highlight_max=True)

# Italicise party/group labels; bold the focus (highlighted red bar).
style_labels(
    ax,
    italic={"Labour Party", "Momentum", "Saving Labour"},
    bold={"Jeremy Corbyn"},
)

# Values shown in thousands (descriptor reads "'000") — plain integer ticks.
ax.set_xlim(0, 6)
ax.set_xticks([0, 1, 2, 3, 4, 5, 6])

finalize(
    ax,
    title="Left-click",
    descriptor="Average number of likes per Facebook post\n2016, '000",
    source="Source: [Facebook](https://www.facebook.com/)",
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
)

out = Path(__file__).resolve().parent / "corbyn.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Corbyn chart")
