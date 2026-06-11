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

Values are computed from the GSS 1972-2024 cumulative microdata
(weighted % agreeing, split by birth cohort), smoothed with a cubic
Hermite pass so the biennial wiggles render as the reference's soft
curves.
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


# GSS asked the gay-marriage question (MARHOMO/marsame) in 1988, then
# biennially 2004-18. Values below are the % agreeing, computed directly
# from the GSS 1972-2024 cumulative microdata (wtssall-weighted, share
# answering "strongly agree"/"agree") split by birth cohort:
#   Millennial & Gen Z 1981+, Gen X 1965-80, Boomer 1946-64,
#   Silent 1928-45, Greatest <1928.
# The 1988 point is kept separate: the 16-year gap to 2004 renders as a
# straight, lighter segment. The Greatest cohort is unreportable after
# 2014 (cell sizes < 25), so its line stops there.
years = np.array([2004, 2006, 2008, 2010, 2012, 2014, 2016, 2018])
years_greatest = np.array([2004, 2006, 2008, 2010, 2012, 2014])

series = {
    "millennial": (years, [50.8, 47.3, 51.3, 64.7, 63.6, 71.0, 74.6, 78.4]),
    "genx": (years, [37.1, 41.5, 49.2, 48.3, 52.8, 58.2, 56.7, 68.4]),
    "boomer": (years, [25.5, 33.8, 33.8, 41.1, 42.6, 50.8, 53.2, 58.7]),
    "silent": (years, [23.2, 20.0, 21.8, 35.8, 30.1, 39.6, 46.8, 46.9]),
    "greatest": (years_greatest, [17.6, 24.6, 26.7, 25.9, 26.9, 28.0]),
    "average": (years, [30.9, 35.5, 39.2, 46.5, 48.9, 56.8, 59.2, 68.2]),
}
start_1988 = {"genx": 11.5, "boomer": 13.8, "silent": 9.5, "greatest": 9.4}

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
    [1988, 2004], [11.6, 30.9],
    color=C_SPINE, linewidth=1.7, linestyle=(0, (1, 2.0)), zorder=5,
)
ax.plot(1988, 11.6, "o", color=C_SPINE, markersize=3.6, zorder=5)

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
    2009.8, 72.8, "Millennial & Gen Z",
    color=C_MILL, fontsize=10, fontweight="bold", ha="center", va="bottom", zorder=6,
)
end_labels = [
    (2018.6, "Gen X", C_GENX, 68.5, "bold", 10),
    (2018.6, "Baby-\nboomer", C_BOOMER, 58.5, "bold", 10),
    (2018.6, "Silent", C_SILENT, 46.5, "bold", 10),
    (2014.5, "Greatest", C_GREATEST, 30.5, "bold", 10),
    (2014.5, "(and earlier)", C_GREATEST, 27.1, "normal", 8),
]
for x, text, color, y, weight, size in end_labels:
    ax.text(
        x, y, text,
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

# Left-side explanatory annotation with a thin arrowhead onto the 2004
# fan-out. The label is placed by measuring its rendered extent and
# lifting it until its baseline clears the rising cohort segments below,
# so a long note never crowds the lines (the reviewer's ask).
_TX, _TY = 1988.6, 33.0
ann = ax.annotate(
    "Support for gay marriage\nhas grown steadily within\nall age groups",
    xy=(2003.6, 37.0),
    xytext=(_TX, _TY),
    color=C_LABEL,
    fontsize=9,
    ha="left",
    va="bottom",
    linespacing=1.35,
    arrowprops=dict(
        arrowstyle="-|>",
        color=C_LABEL,
        lw=0.8,
        shrinkA=6,
        shrinkB=4,
        mutation_scale=10,
        connectionstyle="arc3,rad=-0.22",
        relpos=(1.0, 0.4),
    ),
    zorder=6,
)


def _genx_segment_y(x):
    """The 1988->2004 Gen X segment — the highest line beneath the note."""
    g0, g1 = start_1988["genx"], series["genx"][1][0]
    return g0 + (g1 - g0) * (x - 1988) / (2004 - 1988)


fig.canvas.draw()
_ext = ann.get_window_extent(fig.canvas.get_renderer())
_inv = ax.transData.inverted()
(_bx0, _by0) = _inv.transform((_ext.x0, _ext.y0))
(_bx1, _by1) = _inv.transform((_ext.x1, _ext.y1))
_needed_bottom = max(_genx_segment_y(_bx0), _genx_segment_y(min(_bx1, 2004.0))) + 2.5
if _by0 < _needed_bottom:
    ann.set_position((_TX, _TY + (_needed_bottom - _by0)))

finalize(
    ax,
    title="Public opinion changes as younger generations replace older ones",
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
