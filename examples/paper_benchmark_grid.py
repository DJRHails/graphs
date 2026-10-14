# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Paper figure — a panel grid whose spacing says which way to compare.

After the small multiples in Figure 2 of Wang et al., "Base Models Can Reason
By Taking a Cue From Training Data", re-cut as one row per model (values read
off the published bars, so approximate to ±0.02). ``row_emphasis`` keeps the
gaps inside a row tight and opens the gaps between rows, so the eye compares
one model's conditions across benchmarks before it compares models. Same
``concept_colors`` map as ``paper_cue_bars.py`` — in a paper both scripts
import it from one module.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graphs import (
    C_TEXT,
    concept_colors,
    finalize,
    panel_label,
    right_axis,
    row_emphasis,
    save_chart,
    set_theme,
    subplots,
    top_legend,
)

COLORS = concept_colors({"Base model": "grey", "Cue": "yellow", "After RL": "blue"})
CONDITIONS = ["Base model", "Cue", "After RL"]
BENCHMARKS = ["GSM8K", "AMC 23", "AIME 2024", "HumanEval"]
SCORES = {  # model -> benchmark -> (base, cue, after RL)
    "Olmo-3-7B": [(0.45, 0.87, 0.61), (0.30, 0.60, 0.67), (0.12, 0.24, 0.36), (0.50, 0.70, 0.69)],
    "Qwen3-14B": [(0.85, 0.96, 0.95), (0.46, 0.73, 0.72), (0.10, 0.30, 0.27), (0.87, 0.83, 0.89)],
}

set_theme()
fig, axes = subplots("manuscript", height=5.4, nrows=2, ncols=4, sharey=True)
for row, (model, per_bench) in zip(axes, SCORES.items()):
    for col, (ax, scores) in enumerate(zip(row, per_bench)):
        for x, (concept, value) in enumerate(zip(CONDITIONS, scores)):
            ax.bar(x, value, width=0.75, color=COLORS[concept], label=concept)
        ax.set_xticks([])
        ax.set_ylim(0, 1.0)
        ax.set_yticks([0, 0.5, 1.0])
        if col == len(BENCHMARKS) - 1:
            right_axis(ax)
            ax.tick_params(axis="y", labelright=True)  # sharey hid inner labels
        else:
            ax.tick_params(axis="y", labelleft=False, labelright=False)

row_emphasis(fig)
top_legend(axes[0, 0], *axes[0, 0].get_legend_handles_labels(), ncol=3)
finalize(
    axes[0, 0],
    title="Does the cue's gain hold across benchmarks?",
    descriptor="pass@1 by benchmark, one row per model",
    source="Source: Wang et al., token-cue paper, Fig. 2; paper_benchmark_grid.py",
    y_axis_right=False,
    panel_labels=True,
)
for row, model in zip(axes, SCORES):
    for ax, bench in zip(row, BENCHMARKS):
        panel_label(ax, f"{model} · {bench}" if ax is row[0] else bench)
        ax.title.set_color(C_TEXT)

save_chart(__file__, deck=True, formats=("png", "pdf"))
