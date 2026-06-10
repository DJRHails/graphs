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
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from graphs import (
    C_RED_BRAND,
    finalize,
    footnotes,
    get_font,
    set_theme,
    top_legend,
)
from graphs._superscript import render_text_with_superscripts

set_theme()

FP_LABEL = fm.FontProperties(family=get_font(), weight="normal")
FP_VALUE = fm.FontProperties(family=get_font(), weight="bold")

C_IWG = "#ef8d87"   # lighter companion tint for the paired series
C_BAND = "#D9E6ED"  # pale blue row band sampled from the original
C_ZERO = "#1A1A1A"  # dark zero baseline at the start of each bar pair

# (category label, WeWork value, IWG value, WeWork label, IWG label)
PANELS = [
    ("Total assets*", 27.0, 11.1, "27", "11.1"),
    ("Revenue", 1.8, 3.4, "1.8", "3.4"),
    ("Net profit/\nloss", -1.9, 0.1, "-1.9", "0.1"),
    ("Market\ncapitalisation†", 47.0, 4.5, "47‡", "4.5"),
]

fig, axes = plt.subplots(4, 1, figsize=(4.6, 4.7))
fig.subplots_adjust(top=0.76, bottom=0.12, left=0.245, right=0.945, hspace=0.38)


def value_label(ax, value: float, text: str, y: float, span: float) -> None:
    """Label a bar: white inside at the zero end, or tinted outside the tip."""
    pos = ax.get_position()
    axis_width_in = ax.figure.get_figwidth() * pos.width
    pad = 3.5 * span / (axis_width_in * 72)  # 3.5pt converted to data units
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
    ax.set_xlim(lo, hi)
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
    marker="rule",
    descriptor="Shared workspace providers, 2018, $bn",
    source="",
    title_x=0.02,
    y_start=0.035,
    autoscale_y=False,
    auto_layout=False,  # stacked bands need explicit hspace
)

# Category labels sit on the pale band, which extends left of each bar pair.
BAND_X0 = 0.02  # flush with the title's left edge
for ax, (label, *_rest) in zip(axes, PANELS, strict=True):
    pos = ax.get_position()
    fig.add_artist(plt.Rectangle(
        (BAND_X0, pos.y0), pos.x0 - BAND_X0, pos.height,
        transform=fig.transFigure, facecolor=C_BAND, edgecolor="none", zorder=0.5,
    ))
    render_text_with_superscripts(
        fig,
        BAND_X0 + 0.01,
        (pos.y0 + pos.y1) / 2,
        label,
        fontsize=9,
        fontproperties=FP_LABEL,
        color="#1A1A1A",
        va="center",
        ha="left",
    )

handles = [Patch(facecolor=C_RED_BRAND), Patch(facecolor=C_IWG)]
top_legend(
    fig,
    handles,
    ["WeWork", "IWG"],
    align="right",
    x=axes[0].get_position().x1,
    y=0.90,
    ncol=1,
    fontsize=8,
    handlelength=0.9,
)

footnotes(
    fig,
    "*End June 2019",
    "†Latest",
    "‡Estimate",
    source="Sources: Bloomberg; company reports",
    max_width_frac=0.6,  # force the notes onto their own row above the source
)

out = Path(__file__).resolve().parent / "wework.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved WeWork chart")
