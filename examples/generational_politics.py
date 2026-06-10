# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Public opinion changes as younger
generations replace older ones" generational-replacement chart.

Five generation lines plus a dotted national average track the share of
Americans agreeing that "Gay people should be allowed to get married"
(General Social Survey: asked in 1988, then biennially from 2004).
Younger generations sit higher; the dotted average climbs as cohort
replacement does its work. Reds for the younger cohorts, blues for the
older ones; in-chart labels at the line ends replace a legend.

Values are read off the published chart, smoothed with a cubic Hermite
pass so the biennial wiggles render as the reference's soft curves.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from graphs import (
    C_GRID,
    C_LABEL,
    C_RED,
    C_SPINE,
    PALETTE,
    finalize,
    footnotes,
    set_theme,
)

set_theme()


def _pchip_slopes(x, y):
    """Fritsch-Carlson monotone tangents (PCHIP, no scipy dependency).

    Shape-preserving: keeps the long 1988→2004 survey gap straight and
    rounds the biennial wiggles without overshoot.
    """
    h = np.diff(x)
    s = np.diff(y) / h
    m = np.zeros_like(y)
    for i in range(1, len(y) - 1):
        if s[i - 1] * s[i] > 0:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / s[i - 1] + w2 / s[i])
    m[0] = s[0]
    m[-1] = s[-1]
    return m


def hermite_smooth(x, y, samples_per_seg=24):
    """Cubic Hermite interpolation through survey points with PCHIP tangents."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    slopes = _pchip_slopes(x, y)
    xs_out, ys_out = [], []
    for i in range(len(x) - 1):
        h = x[i + 1] - x[i]
        t = np.linspace(0, 1, samples_per_seg, endpoint=(i == len(x) - 2))
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        xs_out.append(x[i] + t * h)
        ys_out.append(
            h00 * y[i] + h10 * h * slopes[i] + h01 * y[i + 1] + h11 * h * slopes[i + 1]
        )
    return np.concatenate(xs_out), np.concatenate(ys_out)


# GSS asked the gay-marriage question in 1988, then biennially 2004-18.
# Values are % agreeing, read off the published chart. The 1988 point is
# kept separate: the 16-year gap renders as a straight, lighter segment.
years = np.array([2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018])
years_mill = np.array([2006, 2008, 2010, 2012, 2014, 2016, 2018])

series = {
    "millennial": (years_mill, [49.5, 47.5, 57.0, 60.0, 67.0, 71.0, 76.5]),
    "genx": (years, [37.0, 42.0, 46.5, 49.0, 47.5, 56.0, 60.0, 66.0]),
    "boomer": (years, [26.0, 30.0, 32.0, 38.0, 42.0, 48.0, 52.0, 56.0]),
    "silent": (years, [22.0, 19.5, 26.5, 33.0, 27.5, 35.0, 38.0, 42.0]),
    "greatest": (years, [23.0, 33.5, 31.0, 21.5, 23.5, 35.0, 29.5, 30.5]),
    "average": (years, [30.0, 35.0, 39.0, 46.0, 49.0, 57.0, 59.0, 63.0]),
}
start_1988 = {"genx": 17.0, "boomer": 12.0, "silent": 11.0, "greatest": 10.0}

C_MILL = C_RED
C_GENX = "#e2656c"  # lighter red, one step down from the accent
C_BOOMER = "#80bcb4"  # pale teal
C_SILENT = "#4f93b8"  # mid steel blue
C_GREATEST = PALETTE["blue"]


def lighten(color, frac=0.35):
    """Blend a hex colour toward white by ``frac`` (reference renders the
    interpolated 1988→2004 survey-gap segment in a lighter tint)."""
    rgb = [int(color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(c + (255 - c) * frac):02x}" for c in rgb)


fig, ax = plt.subplots(figsize=(6.1, 5.7))

line_specs = [
    ("genx", C_GENX, 1.9),
    ("boomer", C_BOOMER, 1.9),
    ("silent", C_SILENT, 1.9),
    ("greatest", C_GREATEST, 1.9),
    ("millennial", C_MILL, 2.4),
]
for key, color, lw in line_specs:
    xs, ys = series[key]
    sx, sy = hermite_smooth(xs, ys)
    ax.plot(sx, sy, color=color, linewidth=lw, zorder=4, solid_capstyle="round")
    if key in start_1988:
        pale = lighten(color)
        ax.plot([1988, 2004], [start_1988[key], ys[0]], color=pale, linewidth=lw, zorder=3)
        ax.plot(1988, start_1988[key], "o", color=pale, markersize=3.6, zorder=5)
    else:
        ax.plot(xs[0], ys[0], "o", color=color, markersize=4.2, zorder=5)

# National average: dotted near-black line (full strength across the gap),
# dot marker at the 1988 point.
avg_x, avg_y = series["average"]
sx, sy = hermite_smooth(avg_x, avg_y)
ax.plot(sx, sy, color=C_SPINE, linewidth=1.7, linestyle=(0, (1, 2.0)), zorder=5)
ax.plot(
    [1988, 2004], [13.0, 30.0],
    color=C_SPINE, linewidth=1.7, linestyle=(0, (1, 2.0)), zorder=5,
)
ax.plot(1988, 13.0, "o", color=C_SPINE, markersize=3.6, zorder=5)

# Axis cosmetics — 0/25/75 labelled, 50 gridline left silent so the
# series labels at the right edge stay clean (matches the reference).
ax.set_xlim(1984, 2021.5)
ax.set_ylim(0, 82)
ax.set_xticks([1985, 1990, 1995, 2000, 2005, 2010, 2015, 2018])
ax.set_xticklabels(["1985", "90", "", "2000", "", "10", "", "18"])
ax.set_yticks([0, 25, 50, 75])
ax.set_yticklabels(["0", "25", "", "75"])
ax.grid(axis="x", visible=False)
ax.grid(axis="y", color=C_GRID, linewidth=0.6, zorder=0)
ax.tick_params(axis="x", length=4, pad=4)

# In-chart series labels: Millennial sits above its line mid-chart, the
# rest hang off the right edge next to their line ends.
ax.text(
    2011.5, 71.5, "Millennial & Gen Z",
    color=C_MILL, fontsize=10, fontweight="bold", ha="center", va="bottom", zorder=6,
)
end_labels = [
    ("Gen X", C_GENX, 67.5, "bold", 10),
    ("Baby-\nboomer", C_BOOMER, 57.0, "bold", 10),
    ("Silent", C_SILENT, 43.5, "bold", 10),
    ("Greatest", C_GREATEST, 32.0, "bold", 10),
    ("(and earlier)", C_GREATEST, 28.6, "normal", 8),
]
for text, color, y, weight, size in end_labels:
    ax.text(
        2018.6, y, text,
        color=color, fontsize=size, fontweight=weight,
        ha="left", va="center", linespacing=1.05, zorder=6,
    )

# "National average" pointer: bold label with a thin drop-line down to
# the dotted line at the 2004 survey wave.
ax.text(
    2003.8, 58.5, "National\naverage",
    color=C_LABEL, fontsize=9, fontweight="bold",
    ha="center", va="bottom", linespacing=1.1, zorder=6,
)
ax.plot([2003.8, 2003.8], [57.0, 32.0], color=C_LABEL, linewidth=0.6, zorder=3)

# Left-side annotation with a curved arrow onto the Gen X line.
ax.annotate(
    "Support for gay marriage\nhas grown steadily within\nall age groups",
    xy=(2003.4, 36.2),
    xytext=(1989.5, 28.0),
    color=C_LABEL,
    fontsize=8.5,
    ha="left",
    va="center",
    linespacing=1.35,
    arrowprops=dict(
        arrowstyle="-",
        color=C_LABEL,
        lw=0.7,
        shrinkA=4,
        shrinkB=2,
        connectionstyle="arc3,rad=-0.22",
        relpos=(1.0, 0.95),
    ),
    zorder=6,
)

finalize(
    ax,
    title="Public opinion changes as younger generations replace older ones",
    marker="rule",
    descriptor=(
        "United States, % agreeing by generation\n"
        "“Gay people should be allowed to get married”"
    ),
    source="",
    y_axis_right=True,
    autoscale_y=False,
    footnote_lines=1,
)
footnotes(
    fig,
    source=(
        "Sources: [General Social Survey](https://gss.norc.org/); "
        "[The Economist](https://www.economist.com/)"
    ),
)

out = Path(__file__).resolve().parent / "generational_politics.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved generational politics chart")
