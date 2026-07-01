"""graphs — Economist-style chart theme for matplotlib/seaborn.

Usage::

    from graphs import set_theme, finalize, colors
    set_theme()

    fig, ax = plt.subplots()
    fig.subplots_adjust(top=0.68, bottom=0.14, left=0.06, right=0.88)
    ax.plot(...)
    finalize(ax, title="Bold headline", descriptor="Country, metric, unit",
             source="Source: Organisation")

Project overrides versus the styleguide:

* backgrounds are transparent (use ``set_theme(bg=C_BG_TINT)`` for the
  styleguide pale blue-grey)
* accent red is ``C_RED`` (``#bf352b``); ``C_RED_BRAND`` and ``C_RED_DATA``
  expose the styleguide hexes if you need them
* typography is IBM Plex Sans + IBM Plex Sans Condensed
"""

from graphs._annotations import (
    broken_axis,
    callout,
    direction_label,
    highlight_label,
    highlight_panel,
    index_marker,
    number_box,
    threshold_arrows,
)
from graphs._charts import (
    bar_h,
    bar_sublabels,
    bar_v,
    bar_value_labels,
    bump_chart,
    ci_fill,
    color_axis,
    dot_plot,
    dumbbell,
    pie_marker,
    right_axis,
    scatter_category,
    scatter_highlight,
    scatter_standard,
    smoothed_line,
    thermometer,
    threshold_lollipop,
    trend_line,
)
from graphs._finalize import (
    dark_zero_line,
    finalize,
    footnotes,
    panel_label,
    save_chart,
    verify_layout,
    x_axis_label,
    x_axis_top,
    y_axis_label,
    year_axis,
    year_ticks,
)
from graphs._fonts import _get_font as get_font
from graphs._fonts import _get_font_condensed as get_font_condensed
from graphs._format import format_count, magnitude_word, scale_axis
from graphs._labels import (
    inset_tick_labels,
    italicize_labels,
    label_lines,
    style_labels,
    y_labels_on_grid,
)
from graphs._legend import smart_legend, top_legend
from graphs._palette import (
    C_BG,
    C_BG_TINT,
    C_BG_TRANSPARENT,
    C_BOX_FILL,
    C_CI,
    C_GRID,
    C_HIGHLIGHT_PANEL,
    C_HIGHLIGHT_PANEL_RED,
    C_LABEL,
    C_LABEL_MUTED,
    C_OTHER,
    C_RED,
    C_RED_BRAND,
    C_RED_DATA,
    C_SOURCE,
    C_SPINE,
    C_TEXT,
    PALETTE,
    colors,
    cycle_for,
    snapshot_palette,
)
from graphs._theme import FORMATS, set_theme, subplots

__version__ = "0.6.4"

__all__ = [
    # theme + finalize
    "set_theme",
    "subplots",
    "FORMATS",
    "finalize",
    "dark_zero_line",
    "footnotes",
    "panel_label",
    "save_chart",
    "verify_layout",
    "x_axis_label",
    "x_axis_top",
    "y_axis_label",
    "year_axis",
    "year_ticks",
    # palette
    "PALETTE",
    "colors",
    "cycle_for",
    "snapshot_palette",
    "C_BG",
    "C_BG_TINT",
    "C_BG_TRANSPARENT",
    "C_BOX_FILL",
    "C_CI",
    "C_GRID",
    "C_HIGHLIGHT_PANEL",
    "C_HIGHLIGHT_PANEL_RED",
    "C_LABEL",
    "C_LABEL_MUTED",
    "C_OTHER",
    "C_RED",
    "C_RED_BRAND",
    "C_RED_DATA",
    "C_SOURCE",
    "C_SPINE",
    "C_TEXT",
    # charts
    "bar_h",
    "bar_v",
    "bar_value_labels",
    "bar_sublabels",
    "bump_chart",
    "ci_fill",
    "color_axis",
    "dot_plot",
    "dumbbell",
    "pie_marker",
    "right_axis",
    "thermometer",
    "threshold_lollipop",
    "scatter_standard",
    "scatter_highlight",
    "scatter_category",
    "smoothed_line",
    "trend_line",
    # annotations
    "callout",
    "direction_label",
    "highlight_panel",
    "highlight_label",
    "index_marker",
    "broken_axis",
    "number_box",
    "threshold_arrows",
    # labels & legends
    "inset_tick_labels",
    "italicize_labels",
    "style_labels",
    "label_lines",
    "y_labels_on_grid",
    "smart_legend",
    "top_legend",
    # fonts
    "get_font",
    "get_font_condensed",
    # formatting
    "format_count",
    "magnitude_word",
    "scale_axis",
]
