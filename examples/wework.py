# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Replica: Economist daily chart "Is WeWork working?".

Four metric panels comparing WeWork against IWG (Regus's parent), 2018, $bn.
Each panel is its own axes with a pale box-fill band and a per-panel x-scale,
so the larger value always spans the full band width. Values are labelled
inside the bar at the zero end, or outside the tip when the bar is too short.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.font_manager as fm
from matplotlib.patches import Patch

from graphs import (
    C_RED_BRAND,
    C_SPINE,
    finalize,
    footnotes,
    get_font,
    save_chart,
    set_theme,
    subplots,
    top_legend,
)
from graphs._superscript import render_text_with_superscripts

set_theme()

FP_LABEL = fm.FontProperties(family=get_font(), weight="normal")
FP_VALUE = fm.FontProperties(family=get_font(), weight="bold")

C_IWG = "#ef8d87"   # lighter companion tint for the paired series
C_BAND = "#D9E6ED"  # pale blue row band sampled from the original
C_ZERO = C_SPINE  # dark zero baseline at the start of each bar pair

# (category label, WeWork value, IWG value, WeWork label, IWG label)
PANELS = [
    ("Total assets*", 27.0, 11.1, "27", "11.1"),
    ("Revenue", 1.8, 3.4, "1.8", "3.4"),
    ("Net profit/\nloss", -1.9, 0.1, "-1.9", "0.1"),
    ("Market\ncapitalisation†", 47.0, 4.5, "47‡", "4.5"),
]

fig, axes = subplots("daily", height=4.7, nrows=4)
# Each panel spans the full band, category-label column included, so the label
# gutter counts as graph; LABEL_COLUMN is its share of the panel width.
LABEL_COLUMN = 0.243
PANEL_GRID = dict(top=0.85, bottom=0.11, left=0.02, right=0.945, hspace=0.38)
# Pre-size the panel band so value_label's data-unit pad is computed against
# roughly the final axes width; finalize re-applies the auto outer margins, and
# the bespoke margins are restored after it (below).
fig.subplots_adjust(**PANEL_GRID)


def value_label(ax, value: float, text: str, y: float, span: float) -> None:
    """Label a bar: white inside at the zero end, or tinted outside the tip."""
    pos = ax.get_position()
    axis_width_in = ax.figure.get_figwidth() * pos.width
    x_lo, x_hi = ax.get_xlim()
    pad = 3.5 * (x_hi - x_lo) / (axis_width_in * 72)  # 3.5pt converted to data units
    if abs(value) / span >= 0.15:
        x, ha = (pad, "left") if value >= 0 else (-pad, "right")
        color = "white"
    else:
        x, ha, color = value + pad, "left", C_IWG
    render_text_with_superscripts(
        ax.figure,
        x,
        y,
        text,
        fontsize=8,
        fontproperties=FP_VALUE,
        color=color,
        va="center",
        ha=ha,
        transform=ax.transData,
    )


Y_LO, Y_HI = -0.72, 1.72  # near-contiguous bars with a thin band margin

for ax, (label, ww, iwg, ww_text, iwg_text) in zip(axes, PANELS, strict=True):
    lo = min(0.0, ww, iwg)
    hi = max(0.0, ww, iwg)
    ax.barh([1, 0], [ww, iwg], color=[C_RED_BRAND, C_IWG], height=0.92, zorder=2)
    ax.set_xlim(lo - LABEL_COLUMN / (1 - LABEL_COLUMN) * (hi - lo), hi)
    ax.set_ylim(Y_LO, Y_HI)
    ax.set_facecolor(C_BAND)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(visible=False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Dark baseline at zero, where the bar pair starts.
    ax.plot([0, 0], [Y_LO, Y_HI], color=C_ZERO, linewidth=1.0,
            solid_capstyle="butt", clip_on=False, zorder=3)

    value_label(ax, ww, ww_text, 1, hi - lo)
    value_label(ax, iwg, iwg_text, 0, hi - lo)

finalize(
    axes[0],
    title="Is WeWork working?",
    descriptor="Shared workspace providers, 2018, $bn",
    source="",
    title_x=0.02,
    y_start=0.035,
    autoscale_y=False,
)
# REMAINING EDGE CASE — a manual subplots_adjust survives here on purpose.
# This chart writes its category labels and bar value labels AFTER finalize,
# so finalize can't measure them: there are no y-tick labels to size the grid
# from, and the value labels don't exist yet when the right is measured. Pin
# the bespoke band + hspace so those post-finalize artists land right.
fig.subplots_adjust(**PANEL_GRID)

# Category labels sit in each panel's left column, on the pale band.
for ax, (label, *_rest) in zip(axes, PANELS, strict=True):
    render_text_with_superscripts(
        fig,
        0.012,
        0.5,
        label,
        fontsize=9,
        fontproperties=FP_LABEL,
        color=C_SPINE,
        va="center",
        ha="left",
        transform=ax.transAxes,
    )

# Colour key top-right, level with the title stack.
handles = [Patch(facecolor=C_RED_BRAND), Patch(facecolor=C_IWG)]
top_legend(
    fig,
    handles,
    ["WeWork", "IWG"],
    align="right",
    x=axes[0].get_position().x1,
    y=0.94,
    ncol=1,
    fontsize=8,
    handlelength=0.9,
)

footnotes(
    fig,
    "*End June 2019; †Latest; ‡Estimate",
    source="Sources: Bloomberg; company reports",
)

save_chart(__file__)
