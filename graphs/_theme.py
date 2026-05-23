"""Economist-style matplotlib/seaborn global theme.

Defaults follow the Economist web styleguide, with two project overrides
documented in ``_palette``:

* backgrounds are transparent (figure + axes + savefig)
* accent red is ``#bf352b`` (not the styleguide ``#E3120B``/``#DB444B``)
"""

import matplotlib.pyplot as plt

from graphs._fonts import _get_font, _get_font_condensed
from graphs._palette import (
    C_BG,
    C_GRID,
    C_LABEL,
    C_LABEL_MUTED,
    C_SPINE,
    C_TEXT,
    colors,
)


def set_theme(*, bg: str | None = None, transparent: bool = False) -> None:
    """Apply The Economist's visual style globally to matplotlib/seaborn.

    Args:
        bg: Override the figure/axes background colour. Defaults to white.
            Pass ``C_BG_TRANSPARENT`` (``"none"``) for a transparent figure
            and savefig, or ``C_BG_TINT`` (``#E9EDF0``) for the styleguide
            pale blue-grey, or any hex string.
        transparent: Whether savefig should write a transparent PNG/PDF.
            Defaults to ``False`` (matches the white default bg). Set
            ``True`` when ``bg`` is also transparent.
    """
    bg = bg if bg is not None else C_BG
    sans = _get_font()
    cnd = _get_font_condensed()
    cond_chain = [cnd, sans, "Verdana", "Arial", "DejaVu Sans"]

    plt.rcParams.update(
        {
            # Figure
            "figure.facecolor": bg,
            "figure.edgecolor": bg,
            "figure.dpi": 150,
            "figure.figsize": (7, 5),
            "savefig.facecolor": bg,
            "savefig.edgecolor": bg,
            "savefig.transparent": transparent,
            # Axes
            "axes.facecolor": bg,
            "axes.edgecolor": C_SPINE,
            "axes.linewidth": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": True,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "axes.axisbelow": True,
            "axes.labelcolor": C_SPINE,
            "axes.labelsize": 9,
            "axes.labelpad": 4,
            "axes.prop_cycle": plt.cycler("color", colors),
            # Grid
            "grid.color": C_GRID,
            "grid.linewidth": 0.6,
            "grid.linestyle": "-",
            # Ticks — same weight and colour for x and y. Black is reserved
            # for the zero-baseline (the bottom spine), never the tick marks.
            "xtick.color": C_LABEL_MUTED,
            "ytick.color": C_LABEL_MUTED,
            "xtick.labelcolor": C_LABEL,
            "ytick.labelcolor": C_LABEL,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.major.size": 3.5,
            "xtick.major.width": 0.8,
            "ytick.major.size": 0,
            "xtick.minor.size": 0,
            "ytick.minor.size": 0,
            "xtick.bottom": True,
            "xtick.direction": "out",
            # Typography — body text uses IBM Plex Sans Condensed
            # (styleguide: everything except the headline is condensed). The
            # title pulls IBM Plex Sans (non-condensed) Bold explicitly in
            # ``finalize``.
            "font.family": "sans-serif",
            "font.sans-serif": cond_chain,
            "text.color": C_TEXT,
            "font.weight": "light",
            # Legend
            "legend.frameon": False,
            "legend.fontsize": 8.5,
            "legend.labelcolor": C_TEXT,
            # Lines & patches
            "lines.linewidth": 2.0,
            "lines.solid_capstyle": "round",
            "patch.edgecolor": "none",
        }
    )
