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
            # Regular (not light): keeps the tick/label characters from reading
            # too thin against the axis rule — matches the Economist's
            # axis-to-text weight ratio (~1.2x).
            "font.weight": "regular",
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


# Standard chart widths, inches. Like a newspaper's column formats: the
# width is fixed by the medium, depth varies by content. Fixed widths keep
# the type-to-chart ratio consistent across a set — at 150 dpi with 12pt
# titles, a 4.6in and a 6.4in chart scaled to the same display width differ
# ~40% in apparent type size, which is what makes a gallery look ragged.
FORMATS: dict[str, float] = {
    "daily": 4.6,  # daily-chart / mobile column (portrait-leaning)
    "wide": 7.0,  # article / landscape format
}
_DEFAULT_HEIGHTS: dict[str, float] = {"daily": 5.2, "wide": 4.4}


def subplots(format: str = "wide", *, height: float | None = None, **kwargs):
    """``plt.subplots`` at a standard chart width.

    Standardises the width (the format); height stays the per-chart
    editorial choice. Defaults: ``daily`` 4.6x5.2in, ``wide`` 7.0x4.4in.

        fig, ax = subplots("daily", height=5.6)
        fig, axes = subplots("wide", ncols=3, sharey=True)

    Args:
        format: ``"daily"`` (4.6in column) or ``"wide"`` (7.0in article).
        height: Figure height in inches; per-format default when omitted.
        **kwargs: Forwarded to ``plt.subplots`` (nrows, ncols, sharex, …).

    Returns:
        ``(fig, ax)`` exactly as ``plt.subplots``.
    """
    if format not in FORMATS:
        raise ValueError(f"format must be one of {sorted(FORMATS)}, got {format!r}")
    if "figsize" in kwargs:
        raise TypeError(
            "subplots() fixes the width via `format`; pass height= instead of figsize="
        )
    width = FORMATS[format]
    h = height if height is not None else _DEFAULT_HEIGHTS[format]
    return plt.subplots(figsize=(width, h), **kwargs)
