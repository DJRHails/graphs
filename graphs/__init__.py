"""graphs — Economist-style chart theme for matplotlib/seaborn.

Usage::

    from graphs import set_theme, finalize, colors
    set_theme()

    fig, ax = plt.subplots()
    fig.subplots_adjust(top=0.68, bottom=0.14, left=0.06, right=0.88)
    ax.plot(...)
    finalize(ax, title="Bold headline", descriptor="Country, metric, unit",
             source="Source: Organisation")
"""

from graphs._charts import bar_h, ci_fill, dumbbell
from graphs._finalize import finalize, panel_label
from graphs._fonts import _get_font as get_font
from graphs._labels import label_lines
from graphs._legend import smart_legend
from graphs._palette import (
    C_BG,
    C_CI,
    C_GRID,
    C_LABEL,
    C_RED,
    C_SPINE,
    C_TEXT,
    colors,
)
from graphs._theme import set_theme

__version__ = "0.1.0"

__all__ = [
    "bar_h",
    "ci_fill",
    "colors",
    "C_BG",
    "C_CI",
    "C_GRID",
    "C_LABEL",
    "C_RED",
    "C_SPINE",
    "C_TEXT",
    "dumbbell",
    "finalize",
    "get_font",
    "label_lines",
    "panel_label",
    "set_theme",
    "smart_legend",
]
