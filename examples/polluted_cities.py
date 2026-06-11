# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: Economist daily chart on the world's most polluted cities.

A ranked table laid out as two side-by-side columns (ranks 1-8 and 9-15):
rank, city, and a colour-graded value chip showing average PM2.5 pollution
in 2018. Chip colours run from bright red (worst) through dusty pink to a
pale blue at the bottom of the ranking, matching the original's gradient.
Row bands highlight Indian cities only — the original leaves the Pakistani
and Chinese rows white so India's dominance of the ranking reads at a glance.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from graphs import C_LABEL, C_SPINE, finalize, footnotes, set_theme

set_theme()

LEFT = [
    (1, "Gurugram, India", 136),
    (2, "Ghaziabad, India", 135),
    (3, "Faisalabad, Pakistan", 130),
    (4, "Faridabad, India", 129),
    (5, "Bhiwadi, India", 125),
    (6, "Noida, India", 124),
    (7, "Patna, India", 120),
    (8, "Hotan, China", 116),
]
RIGHT = [
    (9, "Lucknow, India", 116),
    (10, "Lahore, Pakistan", 115),
    (11, "Delhi, India", 114),
    (12, "Jodhpur, India", 113),
    (13, "Muzaffarpur, India", 110),
    (14, "Varanasi, India", 105),
    (15, "Moradabad, India", 105),
]

# Chip colour ramp sampled from the original: bright red at 136 fading
# through dusty pink to pale blue at 105. (value, (r, g, b)) anchors.
_RAMP = [
    (105, (179, 206, 224)),
    (110, (187, 180, 194)),
    (113, (190, 161, 175)),
    (116, (195, 141, 155)),
    (120, (199, 113, 130)),
    (124, (205, 90, 106)),
    (129, (216, 52, 66)),
    (136, (228, 4, 25)),
]

ROW_BAND = "#E8EEF0"  # pale blue-grey banding, Indian cities only
ROW_FS = 13  # rank, city and chip numbers share one enlarged size


def chip_color(value: float) -> tuple[float, float, float]:
    """Interpolate the sampled red-to-blue ramp at `value`."""
    if value <= _RAMP[0][0]:
        return tuple(c / 255 for c in _RAMP[0][1])
    for (v0, c0), (v1, c1) in zip(_RAMP, _RAMP[1:]):
        if value <= v1:
            t = (value - v0) / (v1 - v0)
            return tuple((a + (b - a) * t) / 255 for a, b in zip(c0, c1))
    return tuple(c / 255 for c in _RAMP[-1][1])


fig, ax = plt.subplots(figsize=(6.0, 5.5))

ax.set_xlim(0, 1)
ax.set_ylim(8.05, -1.55)  # inverted: header band above row 0
# Remove ticks entirely (not just hide) so finalize/footnotes don't measure
# phantom tick labels when placing the source line.
ax.set_xticks([])
ax.set_yticks([])
ax.set_axis_off()

BLOCKS = [((0.0, 0.455), LEFT), ((0.545, 1.0), RIGHT)]
CHIP_W = 0.10
BAND_PAD = 0.05  # white gap between row bands, in row units


# (bold city-name Text, ", Country" suffix) pairs, finished after finalize()
# once the layout is settled and the bold name's width can be measured.
CITY_SUFFIXES: list[tuple[plt.Text, str]] = []


def draw_block(x0: float, x1: float, rows: list[tuple[int, str, int]]) -> None:
    """Draw one table column: header, header rule, banded rows, value chips."""
    rank_x = x0 + 0.012
    city_x = x0 + 0.072
    chip_x = x1 - CHIP_W

    ax.text(rank_x, -0.35, "Rank", fontsize=10, fontweight="bold",
            color=C_SPINE, ha="left", va="bottom")
    ax.text(city_x, -0.35, "City", fontsize=10, fontweight="bold",
            color=C_SPINE, ha="left", va="bottom")
    ax.text(chip_x + CHIP_W / 2, -0.35, "Average\nPollution", fontsize=10,
            fontweight="bold", color=C_SPINE, ha="center", va="bottom",
            linespacing=1.15)
    ax.plot([x0, x1], [-0.15, -0.15], color=C_SPINE, linewidth=0.8,
            solid_capstyle="butt", clip_on=False)

    for i, (rank, city, value) in enumerate(rows):
        y0, y1 = i + BAND_PAD, i + 1 - BAND_PAD
        if city.endswith("India"):
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                                   facecolor=ROW_BAND, edgecolor="none", zorder=1))
        ax.add_patch(Rectangle((chip_x, y0), CHIP_W, y1 - y0,
                               facecolor=chip_color(value), edgecolor="none",
                               zorder=2))
        ax.text(rank_x, i + 0.5, str(rank), fontsize=ROW_FS, fontweight="bold",
                color=C_SPINE, ha="left", va="center", zorder=3)
        name, _, country = city.partition(",")
        name_text = ax.text(city_x, i + 0.5, name, fontsize=ROW_FS,
                            fontweight="bold", color=C_LABEL,
                            ha="left", va="center", zorder=3)
        CITY_SUFFIXES.append((name_text, "," + country))
        ax.text(chip_x + CHIP_W / 2, i + 0.5, str(value), fontsize=ROW_FS,
                fontweight="bold", color="white", ha="center", va="center",
                zorder=3)


for (bx0, bx1), rows in BLOCKS:
    draw_block(bx0, bx1, rows)

finalize(
    ax,
    title="These are the most polluted cities in the world",
    descriptor="2018, micrograms per cubic metre*",
    source="Source: AirVisual World Air Quality Report 2018",
    autoscale_y=False,
    footnote_lines=1,
)

footnotes(fig, "*PM2.5", y=ax.get_position().y0 - 0.030)

# Regular-weight ", Country" suffixes, butted against each bold city name.
# Widths are measured only after finalize() has settled the axes geometry.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
to_data = ax.transData.inverted()
for name_text, suffix in CITY_SUFFIXES:
    right_px = name_text.get_window_extent(renderer).x1
    suffix_x = to_data.transform((right_px, 0))[0]
    ax.text(suffix_x, name_text.get_position()[1], suffix, fontsize=ROW_FS,
            color=C_LABEL, ha="left", va="center", zorder=3)

out = Path(__file__).resolve().parent / "polluted_cities.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved polluted cities chart")
