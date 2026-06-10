# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: Economist daily chart on problem drinkers.

"Alcohol firms depend financially on problem drinkers' dependency" —
Britain, alcohol consumption 2013-14. A pictogram legend defines four
drinker groups (non-drinkers, moderate, hazardous, harmful) and three
stacked 100% horizontal bars break down population share, industry
revenues, and units consumed by group.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from graphs import C_GRID, C_LABEL, C_RED_BRAND, PALETTE, finalize, footnotes, set_theme

set_theme()

C_NON = PALETTE["blue"]  # dark blue — non-drinkers
C_MOD = "#A8C8D6"        # pale blue — moderate
C_HAZ = "#F28789"        # pink — hazardous
C_HARM = C_RED_BRAND     # bright red — harmful
C_MOD_TEXT = "#7FA4B5"   # legible darker shade of the pale-blue group
C_HAZ_TEXT = "#E0777A"   # legible darker shade of the pink group
C_ICON = "#BCD2DD"       # pale blue-grey pictograms

# (printed value, colour) per segment; third row's printed values sum to 101,
# so widths are normalised to keep the bar inside the 0-100 canvas.
ROWS = [
    ("25% of Britons drink hazardous or harmful amounts", "% of people",
     [(16, C_NON), (59, C_MOD), (21, C_HAZ), (4, C_HARM)]),
    ("They account for 68% of industry revenues", "% of revenues",
     [(32, C_MOD), (45, C_HAZ), (23, C_HARM)]),
    ("They drink 78% of all alcohol consumed", "% of units consumed",
     [(23, C_MOD), (48, C_HAZ), (30, C_HARM)]),
]

# (column centre, name, text colour, sub-lines, bold sub-lines?)
GROUPS = [
    (12.5, "Non-drinkers", C_NON, ["0 units per week"], True),
    (37.5, "Moderate", C_MOD_TEXT, ["Average: 4", "Range: 1-14"], False),
    (62.5, "Hazardous", C_HAZ_TEXT, ["Average: 24", "Women: 15-35 /", "Men: 15-50"], False),
    (87.5, "Harmful", C_HARM, ["Average: 73", "Women: 36+ /", "Men: 51+"], False),
]


def tumbler(ax, cx, y0, w=1.9, h=0.052):
    """Pint-glass pictogram — a trapezoid, slightly narrower at the base."""
    verts = [
        (cx - w / 2, y0 + h), (cx + w / 2, y0 + h),
        (cx + w * 0.36, y0), (cx - w * 0.36, y0),
    ]
    ax.add_patch(Polygon(verts, closed=True, facecolor=C_ICON, edgecolor="none"))


def wine_glass(ax, cx, y0, w=2.0, h=0.052):
    """Wine-glass pictogram — triangular bowl, stem, foot."""
    bowl_h = h * 0.58
    bowl = [(cx - w / 2, y0 + h), (cx + w / 2, y0 + h), (cx, y0 + h - bowl_h)]
    ax.add_patch(Polygon(bowl, closed=True, facecolor=C_ICON, edgecolor="none"))
    ax.plot([cx, cx], [y0 + 0.004, y0 + h - bowl_h], color=C_ICON, lw=1.4,
            solid_capstyle="butt", zorder=2)
    ax.plot([cx - w * 0.28, cx + w * 0.28], [y0 + 0.002, y0 + 0.002],
            color=C_ICON, lw=1.6, solid_capstyle="butt", zorder=2)


def bottle(ax, cx, y0, w=1.5, h=0.075):
    """Bottle pictogram — body, tapered shoulder, neck."""
    verts = [
        (cx - w / 2, y0), (cx - w / 2, y0 + h * 0.60),
        (cx - w * 0.17, y0 + h * 0.74), (cx - w * 0.17, y0 + h),
        (cx + w * 0.17, y0 + h), (cx + w * 0.17, y0 + h * 0.74),
        (cx + w / 2, y0 + h * 0.60), (cx + w / 2, y0),
    ]
    ax.add_patch(Polygon(verts, closed=True, facecolor=C_ICON, edgecolor="none"))


fig, ax = plt.subplots(figsize=(6.4, 6.4))

ax.set_xlim(0, 100)
ax.set_ylim(0, 1)
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
for spine in ax.spines.values():
    spine.set_visible(False)

# --- Drinker-group legend strip -------------------------------------------
ICON_BASE = 0.86
for sep_x in (25, 50, 75):
    ax.plot([sep_x, sep_x], [0.70, 1.0], color=C_GRID, lw=0.8, zorder=1)

bottle(ax, 10.8, ICON_BASE, w=2.0, h=0.10)         # non-drinkers: water bottle…
tumbler(ax, 14.2, ICON_BASE, w=2.0, h=0.055)       # …and a small glass
for gx in (36.0, 39.0):                            # moderate: two glasses
    tumbler(ax, gx, ICON_BASE, w=2.2, h=0.06)
for row_y in (ICON_BASE + 0.072, ICON_BASE):       # hazardous: 2x4 glasses
    for i, gx in enumerate((58.2, 61.1, 64.0, 66.9)):
        (tumbler if i < 2 else wine_glass)(ax, gx, row_y, w=2.2, h=0.06)
for gx in (80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0):  # harmful: 7 bottles
    bottle(ax, gx, ICON_BASE, w=1.7, h=0.085)

for cx, name, col, sublines, bold_subs in GROUPS:
    ax.text(cx, 0.815, name, ha="center", va="top", fontsize=10.5,
            fontweight="bold", color=col)
    for j, line in enumerate(sublines):
        ax.text(cx, 0.778 - j * 0.032, line, ha="center", va="top",
                fontsize=8.5, fontweight="bold" if bold_subs else "normal",
                color=col)

# --- Three stacked 100% bars ----------------------------------------------
BAR_H = 0.075
for i, (label, unit, segments) in enumerate(ROWS):
    label_y = 0.595 - i * 0.230
    bar_y = label_y - 0.040 - BAR_H
    ax.text(0, label_y, label, ha="left", va="bottom", fontsize=10.5,
            color=C_LABEL)
    ax.text(100, label_y, unit, ha="right", va="bottom", fontsize=9.5,
            color=C_LABEL)

    total = sum(v for v, _ in segments)
    left = 0.0
    for value, col in segments:
        width = value / total * 100
        ax.add_patch(Polygon(
            [(left, bar_y), (left + width, bar_y),
             (left + width, bar_y + BAR_H), (left, bar_y + BAR_H)],
            closed=True, facecolor=col, edgecolor="none", zorder=2,
        ))
        ax.text(left + 1.0, bar_y + BAR_H / 2, str(value), ha="left",
                va="center", fontsize=9.5, fontweight="bold", color="white",
                zorder=3)
        left += width

finalize(
    ax,
    title="Alcohol firms depend financially on problem drinkers’ dependency",
    marker="rule",
    descriptor="Britain, alcohol consumption, 2013-14, units per week",
    source="",
    y_axis_right=False,
    title_x=0.02,
    autoscale_y=False,
    footnote_lines=1,
)
footnotes(
    fig,
    source="Sources: “How dependent is the alcohol industry on heavy\n"
           "drinking in England?” by A. Bhattacharya et al.; NHS",
    y=ax.get_position().y0 - 0.030,
)

out = Path(__file__).resolve().parent / "alcohol_drinkers.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved alcohol-drinkers chart")
