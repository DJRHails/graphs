# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Faceted line chart with panel labels — The Economist style."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.ticker as ticker
import numpy as np

from graphs import (
    C_LABEL,
    C_RED,
    C_SPINE,
    ci_fill,
    finalize,
    panel_label,
    right_axis,
    save_chart,
    set_theme,
    subplots,
)

set_theme()

np.random.seed(7)
x = np.linspace(-6, 10, 80)
panels = {
    "Economic": np.where(
        x < 0, x * 0.01, np.cumsum(np.random.randn(80) * 0.015)
    ),
    "Violent": np.cumsum(np.random.randn(80) * 0.008),
    "Sexual": np.cumsum(np.random.randn(80) * 0.006),
}

fig, axes = subplots("wide", height=3.9, ncols=3, sharey=False)

for ax, (panel_name, y) in zip(axes, panels.items()):
    ci = np.abs(np.random.randn(len(x))) * 0.025 + 0.01
    ci_fill(ax, x, y - ci, y + ci)
    ax.plot(x, y, color=C_RED, linewidth=2)
    ax.axhline(0, color=C_SPINE, linewidth=0.8, zorder=3)
    ax.scatter([0], [0], color=C_SPINE, s=40, zorder=5)

    right_axis(ax)
    ax.yaxis.set_tick_params(pad=-2, labelsize=8.5)
    ax.set_ylim(-0.22, 0.22)
    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter("%.1f"))
    ax.set_xlabel(
        "Years since cancer diagnosis (1980-2018)",
        fontsize=8,
        color=C_LABEL,
    )

# finalize auto-layouts the outer margins AND the inter-panel wspace (measured
# from the per-panel right-axis labels); the y_start reserves the title-stack.
# Panel labels are then drawn anchored to the final axes positions.
finalize(
    axes[0],
    title=(
        "Denmark, criminal-conviction rate since\n"
        "cancer diagnosis, by type of offense"
    ),
    descriptor="Percentage-point change from baseline",
    source=(
        'Source: "Breaking bad", '
        "American Economics Journal, 2026"
    ),
    y_axis_right=False,
    title_x=0.04,
    y_start=0.075,
)

for ax, panel_name in zip(axes, panels.keys()):
    panel_label(ax, panel_name)

save_chart(__file__)
