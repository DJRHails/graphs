# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Paper figure — one column per model, read down the column.

After the RL learning curves in Figure 3 of Wang et al., "Base Models Can
Reason By Taking a Cue From Training Data" (values read off the published
curves, so approximate to ±0.02). Each column is one model: the curves on top,
their gap underneath. ``column_emphasis`` keeps each column's panels close and
opens the gap between models, so the eye reads curve-then-gap before it
compares models. The same ``concept_colors`` map as the other paper examples
keeps "cue" yellow and "RL" blue across the whole figure set.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.colors import to_rgb

from graphs import (
    C_TEXT,
    column_emphasis,
    concept_colors,
    finalize,
    right_axis,
    save_chart,
    set_theme,
    subplots,
    x_axis_label,
    y_labels_on_grid,
)

COLORS = concept_colors({"Base model": "grey", "Cue": "yellow", "After RL": "blue"})


def ink(color: str) -> tuple[float, float, float]:
    """``color`` darkened enough to read as text on white (yellow especially)."""
    return tuple(0.7 * c for c in to_rgb(color))


STEPS = [0, 50, 100, 150, 200, 250, 300]
PASS_AT_1 = {  # model -> (cue-forced RL, plain RL) per GRPO step
    "Olmo-3-7B": (
        [0.78, 0.80, 0.82, 0.83, 0.84, 0.84, 0.84],
        [0.43, 0.64, 0.78, 0.80, 0.82, 0.83, 0.84],
    ),
    "Qwen3-14B": (
        [0.85, 0.85, 0.86, 0.86, 0.86, 0.87, 0.87],
        [0.71, 0.85, 0.86, 0.86, 0.86, 0.87, 0.86],
    ),
}

set_theme()
fig, axes = subplots(
    "manuscript", height=4.6, nrows=2, ncols=2, sharex=True,
    gridspec_kw={"height_ratios": [3, 2]},
)
for col, (model, (cued, plain)) in enumerate(PASS_AT_1.items()):
    curves, gap = axes[0, col], axes[1, col]
    curves.plot(STEPS, cued, color=COLORS["Cue"], marker="o", markersize=3.5,
                label="Cue-forced RL")
    curves.plot(STEPS, plain, color=COLORS["After RL"], marker="o", markersize=3.5,
                label="RL")
    # Headroom above the top gridline: on-grid labels rest above their line.
    curves.set_ylim(0.4, 1.06)
    curves.set_yticks([0.4, 0.6, 0.8, 1.0])
    # Model name inside the panel's empty top-left: a panel_label heading would
    # reserve a band at every row boundary and split each column apart.
    curves.text(0.02, 0.97, model, transform=curves.transAxes, ha="left", va="top",
                fontsize=10, fontweight="bold", color=C_TEXT)

    gap.bar(STEPS, [100 * (c - p) for c, p in zip(cued, plain)], width=30, color=C_TEXT)
    gap.set_ylim(0, 44)
    gap.set_yticks([0, 20, 40])
    gap.set_xticks(STEPS[::2])
    x_axis_label(gap, "GRPO step")
    for ax in (curves, gap):
        right_axis(ax)

# Direct labels where the two curves are furthest apart, in each concept's colour.
olmo = axes[0, 0]
olmo.text(110, 0.865, "Cue-forced RL", ha="left", va="bottom", fontsize=9,
          color=ink(COLORS["Cue"]))
olmo.text(60, 0.55, "RL", ha="left", va="center", fontsize=9, color=ink(COLORS["After RL"]))

column_emphasis(fig)
finalize(
    olmo,
    title="Does forcing the cue make RL training more efficient?",
    descriptor="MATH-500 pass@1 (top); cue-forced minus RL, points (bottom)",
    source="Source: Wang et al., token-cue paper, Fig. 3; paper_training_curves.py",
    y_axis_right=False,
)
for ax in axes.flat:
    y_labels_on_grid(ax)

save_chart(__file__, deck=True, formats=("png", "pdf"))
