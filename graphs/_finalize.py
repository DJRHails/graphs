"""Chart finalisation — title stack, source line, panel labels."""

import warnings

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from graphs._fonts import _get_font
from graphs._palette import C_BG, C_LABEL, C_RED, C_SPINE, C_TEXT


def _check_x_monotonic(ax) -> None:
    """Warn if the x-axis runs right-to-left (e.g. accidental invert_xaxis)."""
    x0, x1 = ax.get_xlim()
    if x0 > x1:
        warnings.warn(
            "graphs.finalize: x-axis runs right-to-left "
            f"(xlim={x0:.3g} → {x1:.3g}). If this is unintended, remove the "
            "invert_xaxis() call or fix the data order.",
            stacklevel=3,
        )


def _autoscale_y(ax, *, headroom: float = 0.10, floor_frac: float = 0.40) -> None:
    """Tighten y-limits when data uses less than `floor_frac` of the range.

    Leaves an explicit user-set y-limit alone (detected by the autoscale flag).
    Skips axes with no real data extent. Adds `headroom` proportional padding
    above the data so the top line/bar doesn't collide with the spine.
    """
    if not ax.get_autoscaley_on():
        return  # user pinned ylim explicitly

    data_max = float("-inf")
    data_min = float("inf")
    for art in list(ax.lines) + list(ax.patches) + list(ax.collections):
        try:
            dp = art.get_datalim(ax.transData) if hasattr(art, "get_datalim") else None
        except Exception:
            dp = None
        if dp is not None and dp.height > 0:
            data_min = min(data_min, dp.y0)
            data_max = max(data_max, dp.y1)

    # Fallback: scan line ydata.
    if not (data_max > float("-inf") and data_min < float("inf")):
        for line in ax.lines:
            ys = line.get_ydata()
            if len(ys):
                data_min = min(data_min, float(min(ys)))
                data_max = max(data_max, float(max(ys)))

    if not (data_max > float("-inf") and data_min < float("inf")):
        return
    if data_max == data_min:
        return

    y_lo, y_hi = ax.get_ylim()
    span_used = (data_max - data_min) / (y_hi - y_lo) if y_hi > y_lo else 1.0
    if span_used >= floor_frac:
        return

    pad = (data_max - data_min) * headroom
    new_lo = max(y_lo, data_min - pad) if data_min >= 0 else data_min - pad
    # Snap to 0 if data is non-negative and close to 0 — keeps the baseline clean.
    if data_min >= 0 and data_min <= (data_max - data_min) * 0.25:
        new_lo = 0.0
    new_hi = data_max + pad
    ax.set_ylim(new_lo, new_hi)


def finalize(
    ax,
    title: str = "",
    descriptor: str = "",
    source: str = "",
    *,
    y_axis_right: bool = True,
    title_x: float | None = None,
    y_start: float = 0.010,
    autoscale_y: bool = True,
):
    """Add Economist finishing touches to an axes object.

    Title stack (top to bottom)::

        ────        short red rule
        Title       IBM Plex Sans Bold
        Descriptor  IBM Plex Sans Regular

    Args:
        title: Chart headline.
        descriptor: Subtitle line (country, metric, unit).
        source: Attribution line below the chart.
        y_axis_right: Move y-axis labels to the right.
        title_x: Override x anchor in figure coords.
            Defaults to the axes bounding-box x0.
            Set to e.g. 0.02 for charts with wide left margins.
        y_start: Gap above bbox.y1 where title stack begins.
            Increase to ~0.07 for faceted charts.
        autoscale_y: If True (default), auto-tighten y-limits when the data
            fills less than 40% of the current axis range. Disable for charts
            that need a pinned 0–100% canvas regardless of data.
    """
    fig = ax.get_figure()
    fig.patch.set_facecolor(C_BG)

    _check_x_monotonic(ax)
    if autoscale_y:
        _autoscale_y(ax)

    if y_axis_right:
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.spines["right"].set_visible(True)
        ax.spines["right"].set_color(C_BG)
        ax.spines["right"].set_linewidth(0)
        ax.spines["left"].set_visible(False)

    ax.yaxis.set_tick_params(pad=4, labelsize=9)
    ax.spines["bottom"].set_color(C_SPINE)
    ax.spines["bottom"].set_linewidth(1.0)

    fig.canvas.draw()
    bbox = ax.get_position()
    tx = title_x if title_x is not None else bbox.x0

    # Build title stack upward from just above the axes
    line_gap = 0.013
    rule_gap = 0.026
    y_cursor = bbox.y1 + y_start

    if descriptor:
        n_desc_lines = descriptor.count("\n") + 1
        fig.text(
            tx,
            y_cursor,
            descriptor,
            transform=fig.transFigure,
            fontsize=9.5,
            fontweight="normal",
            color=C_TEXT,
            va="bottom",
            ha="left",
            linespacing=1.25,
        )
        # 0.032 is the height of one descriptor line in figure coords;
        # add 0.022 per extra line so the title sits clear of the wrap.
        y_cursor += 0.032 + 0.022 * (n_desc_lines - 1) + line_gap

    if title:
        fp = fm.FontProperties(family=_get_font(), weight=700)
        fig.text(
            tx,
            y_cursor,
            title,
            transform=fig.transFigure,
            fontsize=12,
            fontproperties=fp,
            color=C_TEXT,
            va="bottom",
            ha="left",
        )
        y_cursor += 0.040 + rule_gap

    # Short red rule at the top (~80 px wide)
    rule_w = 80 / (fig.get_figwidth() * fig.dpi)
    fig.add_artist(
        plt.Line2D(
            [tx, tx + rule_w],
            [y_cursor, y_cursor],
            transform=fig.transFigure,
            color=C_RED,
            linewidth=3.5,
            solid_capstyle="butt",
            clip_on=False,
        )
    )

    if source:
        # Place source below the lowest of: xlabel, x-tick labels.
        # Wrapped multi-line x-tick labels can extend further down than the
        # xlabel and previously caused the source line to overlap them.
        source_y = bbox.y0 - 0.06
        try:
            renderer = fig.canvas.get_renderer()
            lowest_fig_y = bbox.y0
            xlabel = ax.xaxis.label
            if xlabel.get_text():
                xlbl_bbox = xlabel.get_window_extent(renderer=renderer)
                lowest_fig_y = min(
                    lowest_fig_y,
                    xlbl_bbox.transformed(fig.transFigure.inverted()).y0,
                )
            for tl in ax.get_xticklabels():
                if not tl.get_text():
                    continue
                tl_bb = tl.get_window_extent(renderer=renderer)
                lowest_fig_y = min(
                    lowest_fig_y,
                    tl_bb.transformed(fig.transFigure.inverted()).y0,
                )
            source_y = min(source_y, lowest_fig_y - 0.015)
        except Exception:
            pass
        fig.text(
            tx,
            source_y,
            source,
            transform=fig.transFigure,
            fontsize=7.5,
            color=C_LABEL,
            va="top",
            ha="left",
        )

    return fig, ax


def panel_label(ax, label: str, *, fontsize: int = 10) -> None:
    """Bold panel sub-heading with a short dark rule — for faceted charts.

    Renders above the axes::

        --------
        Economic
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    bbox = ax.get_position()

    rule_w = 35 / (fig.get_figwidth() * fig.dpi)
    fig.add_artist(
        plt.Line2D(
            [bbox.x0, bbox.x0 + rule_w],
            [bbox.y1 + 0.052, bbox.y1 + 0.052],
            transform=fig.transFigure,
            color=C_SPINE,
            linewidth=1.2,
            solid_capstyle="butt",
            clip_on=False,
        )
    )
    fig.text(
        bbox.x0,
        bbox.y1 + 0.010,
        label,
        transform=fig.transFigure,
        fontsize=fontsize,
        fontweight="bold",
        color=C_TEXT,
        va="bottom",
        ha="left",
    )
