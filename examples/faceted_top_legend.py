# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Faceted stacked bars with a shared colour key — hands-off ``top_legend``.

Demonstrates the auto-reserved top-legend band: a single colour key spans
above a row of panels, sitting cleanly between a two-line descriptor and the
panels, with NO ``fig.subplots_adjust`` and NO hand-tuned ``y=`` / ``y_start``
padding. ``top_legend`` is called BEFORE ``finalize``; ``finalize`` measures
the legend, reserves a band for it under the title stack, and re-anchors it to
the final axes top.

The data are synthetic: the composition of false flags raised by an offline
monitor, split by monitoring regime (forced yes/no harm question vs a
calibrated threshold) across two harm domains.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from graphs import (
    PALETTE,
    finalize,
    footnotes,
    panel_label,
    right_axis,
    save_chart,
    set_theme,
    subplots,
    top_legend,
)

set_theme()

REGIMES = ["Forced", "Calibrated"]
# (component, colour, [share in panel-1 regimes], [share in panel-2 regimes])
COMPONENTS = [
    ("Benign-but-alarming", PALETTE["blue"], [5.8, 1.2], [4.1, 0.9]),
    ("Cross-harm mismatch", PALETTE["cyan"], [3.1, 0.6], [5.4, 1.1]),
]
PANELS = ["Privacy & surveillance", "Harassment"]

fig, axes = subplots("wide", height=3.9, ncols=2, sharey=True)

idx = np.arange(len(REGIMES))
for panel_i, ax in enumerate(axes):
    bottom = np.zeros(len(REGIMES))
    for name, color, *shares in COMPONENTS:
        vals = np.array(shares[panel_i], dtype=float)
        ax.bar(idx, vals, 0.62, bottom=bottom, color=color, label=name,
               edgecolor="none", zorder=2)
        bottom += vals
    ax.set_xticks(idx)
    ax.set_xticklabels(REGIMES)
    ax.set_ylim(0, 12)
    ax.tick_params(axis="x", length=0)
    right_axis(ax)

# Hands-off: tag the shared colour key BEFORE finalize. finalize reserves a band
# for it between the descriptor and the panels and re-anchors it to the final
# axes top — no subplots_adjust, no manual y= / y_start padding.
handles, labels = axes[0].get_legend_handles_labels()
top_legend(fig, handles, labels, ncol=len(handles))

finalize(
    axes[0],
    title="Where an over-firing monitor's false flags come from",
    descriptor="Composition of flagged benign transcripts, by regime\n% of sampled traffic",
    source="",
    y_axis_right=False,
    title_x=0.04,
    y_start=0.075,
    autoscale_y=False,
)

for ax, name in zip(axes, PANELS):
    panel_label(ax, name)

footnotes(fig, source="Source: Touchstone cross-harm eval (synthetic), 2026")

save_chart(__file__)
