# /// script
# requires-python = ">=3.12"
# dependencies = ["matplotlib", "numpy"]
# ///
"""Replica of *The Economist*'s "Why are some languages spoken faster than others?".

Two side-by-side ridgeline panels of per-language distributions: syllable
rate (red) and information rate (blue). Languages that pack less
information per syllable (Japanese, Spanish) are spoken faster, so the
information-rate distributions cluster — the original's point.

Each distribution is a Gaussian centred on the real per-language mean
with the real standard deviation, computed from the study's published
raw data (Coupé, Oh, Dediu & Pellegrino, "Different languages, similar
encoding efficiency", Science Advances 2019; supplementary data set
``InfoRateData.csv``). Drawn with plain ``fill_between`` on per-language
baselines.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from graphs import (
    C_LABEL,
    C_SPINE,
    direction_label,
    finalize,
    footnotes,
    panel_label,
    save_chart,
    set_theme,
    subplots,
)

set_theme()

RED_FILL = "#E92A36"   # vivid red sampled from the original
BLUE_FILL = "#80AEC5"  # muted steel blue sampled from the original

# Real per-language means and standard deviations from Coupé et al.
# (2019), computed from the authors' supplementary data (InfoRateData.csv):
# SR = syllables/sec, IR = bits/sec. Each language is one (weight=1, mean,
# sigma) Gaussian, so equal area; the wide distributions (Italian, English)
# render low and broad exactly as in the reference. Listed fast-to-slow.
SYLLABLES = {
    "Japanese": [(1.0, 8.03, 0.52)],
    "Spanish": [(1.0, 7.73, 0.47)],
    "Finnish": [(1.0, 7.17, 0.62)],
    "Italian": [(1.0, 7.16, 1.05)],
    "English": [(1.0, 6.34, 0.67)],
    "Thai": [(1.0, 4.70, 0.48)],
}
INFO_RATE = {
    "Japanese": [(1.0, 40.41, 2.63)],
    "Spanish": [(1.0, 41.96, 2.53)],
    "Finnish": [(1.0, 39.37, 3.41)],
    "Italian": [(1.0, 37.89, 5.55)],
    "English": [(1.0, 44.94, 4.78)],
    "Thai": [(1.0, 33.80, 3.43)],
}

Y_TOP = 6.35  # headroom above the top row for the direction cue
PEAK = 0.72  # tallest peak, in row units


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
        ax.text(x[0], base + 0.42, name, fontsize=10, color=C_LABEL, va="bottom", zorder=5)

    ax.set_xlim(*xlim)
    ax.set_ylim(0, Y_TOP)
    ax.set_yticks([])
    ax.grid(False)
    for side in ("left", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="x", length=3, pad=4)


fig, (ax_syl, ax_bit) = subplots("wide", height=6.6, ncols=2)

ridgeline(ax_syl, SYLLABLES, (3.3, 9.6), RED_FILL)
ax_syl.set_xticks([4, 6, 8])
ridgeline(ax_bit, INFO_RATE, (25, 63), BLUE_FILL)
ax_bit.set_xticks([30, 40, 50, 60])

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

# finalize auto-layouts the outer margins (y_start reserves the title-stack);
# restore the inter-panel wspace afterwards, then draw the panel labels anchored
# to the final axes positions.
finalize(
    ax_syl,
    title="Why are some languages spoken faster than others?",
    descriptor="Syllable rate and information rate in selected languages",
    source="",
    title_x=0.02,
    y_start=0.10,
    y_axis_right=False,
    autoscale_y=False,
)
fig.subplots_adjust(bottom=0.12, wspace=0.22)

panel_label(ax_syl, "Syllables per second")
panel_label(ax_bit, "Information rate, bits per second")

footnotes(
    fig,
    source=(
        "Source: Coupé et al., "
        "[Science Advances (2019)](https://doi.org/10.1126/sciadv.aaw2594)"
    ),
)

save_chart(__file__)
