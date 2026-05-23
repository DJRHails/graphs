# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Redesign: euro-area current-account and budget balances.

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few".
The original stacked ten countries with so many colours the message became
illegible. The redesign keeps the four countries the column called out
(Germany, Greece, Netherlands, Spain) plus an aggregated "Others" bucket
for the remaining euro-area members.

Stacked bars per year, two side-by-side panels — one for current-account
balance, one for budget balance.
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from examples._data import load_csv_lines
from graphs import PALETTE, finalize, footnotes, panel_label, right_axis, set_theme, top_legend

set_theme()

FEATURED = ["Germany", "Netherlands", "Spain", "Greece"]
FEATURED_COLORS = {
    "Germany": PALETTE["blue"],
    "Netherlands": PALETTE["cyan"],
    "Spain": PALETTE["yellow"],
    "Greece": PALETTE["red"],
}
OTHERS_COLOR = PALETTE["grey"]

URL = "http://infographics.economist.com/databank/Economist_eu-balance.csv"
reader = list(csv.reader(load_csv_lines(URL)))

years = [int(y) for y in reader[1][1:8]]  # 2009–2015
country_rows = reader[2:22]  # 20 countries

ca = {}  # country -> [7 values]  current-account
bb = {}  # country -> [7 values]  budget balance
for row in country_rows:
    if not row or not row[0]:
        continue
    name = row[0].strip()
    ca[name] = [float(v) / 1000 if v else 0.0 for v in row[1:8]]    # → € billion
    bb[name] = [float(v) / 1000 if v else 0.0 for v in row[8:15]]   # → € billion


def split(d: dict[str, list[float]]) -> tuple[dict, list[float]]:
    """Featured countries + an 'Others' aggregate over the rest."""
    featured = {c: d[c] for c in FEATURED if c in d}
    others = [sum(v) for v in zip(*(d[c] for c in d if c not in FEATURED))]
    return featured, others


def stacked(ax, d: dict[str, list[float]], title: str) -> None:
    featured, others = split(d)
    width = 0.7

    pos_base = np.zeros(len(years))
    neg_base = np.zeros(len(years))

    series = [(name, featured[name], FEATURED_COLORS[name]) for name in FEATURED if name in featured]
    series.append(("Others", others, OTHERS_COLOR))

    for name, vals, col in series:
        vals_arr = np.array(vals)
        pos = np.where(vals_arr > 0, vals_arr, 0)
        neg = np.where(vals_arr < 0, vals_arr, 0)
        ax.bar(years, pos, width, bottom=pos_base, color=col, label=name,
               edgecolor="none", zorder=2)
        ax.bar(years, neg, width, bottom=neg_base, color=col,
               edgecolor="none", zorder=2)
        pos_base = pos_base + pos
        neg_base = neg_base + neg

    # Net line — sum across all featured + others.
    total = pos_base + neg_base
    ax.plot(years, total, color="#1A1A1A", linewidth=1.5, marker="o",
            markersize=4, zorder=3, label="Euro-area total")

    panel_label(ax, title)
    ax.axhline(0, color="#1A1A1A", linewidth=0.8, zorder=1)
    ax.set_xticks(years)


fig, (ax_bb, ax_ca) = plt.subplots(1, 2, figsize=(9, 4.8), sharey=False)
fig.subplots_adjust(top=0.62, bottom=0.10, left=0.02, right=0.96, wspace=0.18)

stacked(ax_bb, bb, "Budget balance, € bn")
stacked(ax_ca, ca, "Current-account balance, € bn")

# Right-axis convention applied per panel.
for axis in (ax_bb, ax_ca):
    right_axis(axis)

finalize(
    ax_bb,
    title="Surfeit of surpluses",
    descriptor="Euro-area, €bn",
    source="",
    title_x=0.02,
    y_start=0.24,
    autoscale_y=False,
)

# Single legend just below the title/descriptor, above both panels.
handles, labels = ax_bb.get_legend_handles_labels()
top_legend(fig, handles, labels, y=0.82, ncol=len(handles))

footnotes(fig, source="Source: Eurostat")

out = Path(__file__).resolve().parent / "eu_balance.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved EU-balance chart")
