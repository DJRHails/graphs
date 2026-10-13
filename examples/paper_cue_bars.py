# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib"]
# ///
"""Paper figure — grouped bars where every concept keeps one colour.

After Figure 2 of Wang et al., "Base Models Can Reason By Taking a Cue From
Training Data" (values are the figure's printed bar labels). Shows the paper
conventions: a ``concept_colors`` map carried into the value labels and the
group labels, literal tokens as monospace chips, a two-level x-axis (bars on
major ticks, bracketed groups on minor ticks), and a vector PDF plus the
headline-free ``_deck`` variant for the paper's own caption.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D
from matplotlib.transforms import ScaledTranslation, blended_transform_factory

from graphs import C_TEXT, concept_colors, finalize, save_chart, set_theme, subplots

# One map for the whole paper: every figure imports it.
COLORS = concept_colors({"Base model": "grey", "Cue": "yellow", "After RL": "blue"})

GROUPS = [
    ("Olmo-3-7B", r".\n\n Okay", [0.42, 0.78, 0.75]),
    ("Qwen3-14B", "Alright,", [0.72, 0.87, 0.87]),
]
CONDITIONS = ["Base model", "Cue", "After RL"]
GROUP_STEP = 3.8
BRACKET_DROP_PT = 25  # rule between the bar labels and the group labels
GROUP_PAD_PT = 30  # group labels sit this far below the axis


def shade(color: str, toward: str, amount: float) -> tuple[float, float, float]:
    """Mix ``color`` toward ``toward`` — darker ink for text, paler fill for chips."""
    a, b = to_rgb(color), to_rgb(toward)
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def ink(concept: str) -> tuple[float, float, float]:
    """The concept's colour darkened enough to read as text on white."""
    return shade(COLORS[concept], "#000000", 0.3)


set_theme()
fig, ax = subplots("manuscript", height=3.3)
below_axis = blended_transform_factory(ax.transData, ax.transAxes) + ScaledTranslation(
    0, -BRACKET_DROP_PT / 72, fig.dpi_scale_trans
)

bar_x, bar_labels, group_x, group_labels = [], [], [], []
for g, (model, cue, values) in enumerate(GROUPS):
    xs = [g * GROUP_STEP + i for i in range(3)]
    for x, concept, value in zip(xs, CONDITIONS, values):
        ax.bar(x, value, width=0.72, color=COLORS[concept])
        ax.annotate(f"{value:.2f}", xy=(x, value), xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=9, color=ink(concept))
    ax.text(xs[1], 1.1, model, ha="center", va="center", fontsize=9.5, fontweight="bold",
            color=C_TEXT)
    bar_x += xs
    bar_labels += ["No cue", cue, "No cue"]
    for (x0, x1), concept in (((xs[0], xs[1]), "Base model"), ((xs[2], xs[2]), "After RL")):
        ax.add_line(Line2D([x0 - 0.4, x1 + 0.4], [0, 0], transform=below_axis,
                           color=ink(concept), linewidth=1.0, clip_on=False))
        group_x.append((x0 + x1) / 2)
        group_labels.append(concept)

ax.set_xticks(bar_x, bar_labels)
ax.set_xticks(group_x, group_labels, minor=True)
ax.xaxis.remove_overlapping_locs = False  # "After RL" sits under its own bar
ax.tick_params(axis="x", which="major", length=0, pad=6)
ax.tick_params(axis="x", which="minor", length=0, pad=GROUP_PAD_PT, labelsize=9)
for label, text in zip(ax.get_xticklabels(), bar_labels):
    if text != "No cue":
        label.set_fontfamily("monospace")
        label.set_bbox({"boxstyle": "round,pad=0.25,rounding_size=0.15",
                        "facecolor": shade(COLORS["Cue"], "#ffffff", 0.75),
                        "edgecolor": COLORS["Cue"], "linewidth": 0.8})
for label, concept in zip(ax.get_xticklabels(minor=True), group_labels):
    label.set_color(ink(concept))

ax.set_ylim(0, 1.18)
ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

finalize(
    ax,
    title="Can a token cue match RL post-training?",
    descriptor="MATH-500 pass@1",
    source="Source: Wang et al., token-cue paper, Fig. 2 (MATH-500, N=500); paper_cue_bars.py",
)

save_chart(__file__, deck=True, formats=("png", "pdf"))
