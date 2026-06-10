# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Why are some languages spoken faster than others?".

Two side-by-side ridgeline panels of per-language distributions: syllable
rate (red) and information rate (blue). Languages that pack less
information per syllable (Japanese, Spanish) are spoken faster, so the
information-rate distributions cluster — the original's point.

Distributions are approximated from the chart as small Gaussian mixtures
(the underlying study is Coupé et al., Science Advances 2019), drawn with
plain ``fill_between`` on per-language baselines.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np

from graphs import (
    C_LABEL,
    C_SPINE,
    direction_label,
    finalize,
    footnotes,
    panel_label,
    set_theme,
)

set_theme()

RED_FILL = "#E92A36"   # vivid red sampled from the original
BLUE_FILL = "#80AEC5"  # muted steel blue sampled from the original

# Each language maps to a list of (weight, mean, sigma) Gaussian components
# eyeballed from the reference shapes. Weights sum to 1, so every language
# has equal area and broad distributions (Italian, English) sit low.
SYLLABLES = {
    "Japanese": [(0.78, 8.10, 0.48), (0.22, 7.00, 0.75)],
    "Spanish": [(0.78, 7.70, 0.48), (0.22, 6.80, 0.65)],
    "Finnish": [(0.90, 7.25, 0.45), (0.10, 4.90, 0.45)],
    "Italian": [(0.65, 7.00, 0.85), (0.35, 5.70, 1.00)],
    "English": [(0.80, 6.20, 0.65), (0.20, 7.40, 0.85)],
    "Thai": [(0.40, 4.18, 0.26), (0.60, 4.92, 0.33)],
}
INFO_RATE = {
    "Japanese": [(0.80, 38.5, 2.2), (0.20, 42.5, 3.0)],
    "Spanish": [(0.72, 42.8, 1.6), (0.28, 39.3, 1.8)],
    "Finnish": [(0.90, 40.5, 2.0), (0.10, 31.5, 1.6)],
    "Italian": [(0.55, 39.5, 3.2), (0.45, 45.0, 4.0)],
    "English": [(0.74, 45.8, 3.3), (0.26, 55.5, 2.6)],
    "Thai": [(0.38, 30.8, 1.6), (0.62, 35.3, 2.1)],
}

Y_TOP = 6.35  # headroom above the top row for the direction cue
PEAK = 0.85  # tallest peak, in row units


def mixture_pdf(x, components):
    """Evaluate a unit-area Gaussian-mixture density on ``x``."""
    pdf = np.zeros_like(x)
    for w, mu, sigma in components:
        pdf += w * np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
    return pdf


def ridgeline(ax, langs, xlim, fill):
    """Draw one panel: a baseline + filled density per language, top to bottom."""
    x = np.linspace(*xlim, 400)
    densities = {name: mixture_pdf(x, comps) for name, comps in langs.items()}
    scale = PEAK / max(d.max() for d in densities.values())

    for i, (name, density) in enumerate(densities.items()):
        base = len(langs) - 1 - i  # first language on the top row
        ax.fill_between(x, base, base + density * scale, color=fill, linewidth=0, zorder=3)
        ax.hlines(base, *xlim, color=C_SPINE, linewidth=0.8, zorder=4)
        ax.text(x[0], base + 0.42, name, fontsize=9.5, color=C_LABEL, va="bottom", zorder=5)

    ax.set_xlim(*xlim)
    ax.set_ylim(0, Y_TOP)
    ax.set_yticks([])
    ax.grid(False)
    for side in ("left", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", length=3, pad=4)


fig, (ax_syl, ax_bit) = plt.subplots(1, 2, figsize=(7.4, 7.0))
fig.subplots_adjust(top=0.80, bottom=0.12, left=0.02, right=0.98, wspace=0.22)

ridgeline(ax_syl, SYLLABLES, (3.3, 9.6), RED_FILL)
ax_syl.set_xticks([4, 6, 8])
ridgeline(ax_bit, INFO_RATE, (25, 63), BLUE_FILL)
ax_bit.set_xticks([30, 40, 50, 60])

panel_label(ax_syl, "Syllables per second")
panel_label(ax_bit, "Information rate, bits per second")

cue_y = 6.02 / Y_TOP
direction_label(
    ax_syl, "Speak more quickly", xy=(1.0, cue_y), arrow="→", placement="after", color=RED_FILL
)
direction_label(
    ax_bit,
    "Convey information more quickly",
    xy=(1.0, cue_y),
    arrow="→",
    placement="after",
    color=BLUE_FILL,
)

finalize(
    ax_syl,
    title="Why are some languages spoken faster than others?",
    marker="rule",
    descriptor="Syllable rate and information rate in selected languages",
    source="",
    title_x=0.02,
    y_start=0.10,
    y_axis_right=False,
    autoscale_y=False,
    auto_layout=False,  # side-by-side panels need explicit wspace
)
footnotes(fig, source="Source: Science Advances (2019)")

out = Path(__file__).resolve().parent / "language_speed.png"
plt.savefig(out, bbox_inches="tight", dpi=150)
plt.close()
print("Saved language-speed chart")
