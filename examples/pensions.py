# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Redesign: pension spending vs. share of population aged 65+.

Replicates the 'good' chart from Sarah Leo's "Mistakes, we've drawn a few".
The original used "50 shades of blue" — colour to mark labelled countries,
which the eye reads as a category. The redesign keeps every dot the same
colour and uses *opacity* (saturation) for emphasis: labelled countries are
fully opaque, the rest are faded. Brazil — the focus country — is bold;
the OECD average is italic.
"""

import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from examples._data import load_csv_lines
from graphs import C_LABEL, C_SPINE, PALETTE, finalize, set_theme, y_axis_label

set_theme()

LABELLED = {
    "Brazil", "Greece", "Italy", "France", "Germany", "Japan",
    "Mexico", "United States", "Britain", "South Korea", "Australia",
}

URL = "http://infographics.economist.com/databank/Economist_pensions.csv"
rows = []
reader = csv.reader(load_csv_lines(URL))
next(reader)
for row in reader:
    if not row or not row[0] or row[0].startswith(("Dates", "Sources")):
        continue
    try:
        rows.append((row[0].strip(), float(row[1]), float(row[2])))
    except ValueError:
        continue

oecd_x = statistics.mean(r[1] for r in rows)
oecd_y = statistics.mean(r[2] for r in rows)

fig, ax = plt.subplots(figsize=(7, 4.8))

# Background: all dots same colour, faded.
faded_x = [r[1] for r in rows if r[0] not in LABELLED]
faded_y = [r[2] for r in rows if r[0] not in LABELLED]
ax.scatter(faded_x, faded_y, s=44, color=PALETTE["blue"], alpha=0.22,
           linewidths=0, zorder=2)

# Foreground: labelled countries — full opacity, same colour.
focus_rows = [r for r in rows if r[0] in LABELLED]
fx = [r[1] for r in focus_rows]
fy = [r[2] for r in focus_rows]
ax.scatter(fx, fy, s=44, color=PALETTE["blue"], alpha=1.0,
           edgecolors=C_SPINE, linewidths=0.8, zorder=3)

# OECD average — same colour, separate marker as a visual cue.
ax.scatter([oecd_x], [oecd_y], s=70, color=PALETTE["blue"],
           edgecolors=C_SPINE, linewidths=0.8, zorder=4)

# Country labels — Brazil bold (focus), OECD italic.
label_offsets = {
    "Brazil": (6, 4), "Greece": (6, -2), "Italy": (6, 4),
    "France": (-6, 6), "Germany": (-6, -10), "Japan": (-6, 4),
    "Mexico": (6, 0), "United States": (6, 2), "Britain": (6, 2),
    "South Korea": (6, -2), "Australia": (6, 2),
}
for name, x, y in focus_rows:
    dx, dy = label_offsets.get(name, (6, 0))
    weight = "bold" if name == "Brazil" else "normal"
    ax.annotate(name, xy=(x, y), xytext=(dx, dy),
                textcoords="offset points",
                fontsize=8, color=C_LABEL, fontweight=weight,
                ha="left" if dx >= 0 else "right")

oecd_fp = fm.FontProperties(family="IBM Plex Sans", style="italic", size=8)
ax.annotate("OECD average", xy=(oecd_x, oecd_y), xytext=(8, -2),
            textcoords="offset points",
            color=C_LABEL, fontproperties=oecd_fp, ha="left")

ax.set_xlim(0, 30)
ax.set_ylim(0, 18)
ax.set_xlabel("Population aged 65+, % of total", color=C_SPINE)

y_axis_label(
    ax,
    "Government spending on pension benefits",
    unit="% of GDP",
)

finalize(
    ax,
    title="Brazil's golden oldie blowout",
    descriptor="Latest available",
    source="Sources: OECD; World Bank; Previdência Social",
    autoscale_y=False,
    y_start=0.050,
)

out = Path(__file__).resolve().parent / "pensions.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved Pensions chart")
