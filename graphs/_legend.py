"""Smart legend placement — pick the emptiest corner of the axes."""

from __future__ import annotations

import warnings
from typing import Sequence

from graphs._palette import C_SPINE

# Legend frame fill — white, not C_BG (which is "none" under the transparent
# theme and would defeat the point of the frame).
_FRAME_FILL = "#FFFFFF"


_CORNERS = {
    "upper right": (1, 1),
    "upper left": (0, 1),
    "lower right": (1, 0),
    "lower left": (0, 0),
}


def smart_legend(
    ax,
    *,
    pad: float = 0.02,
    prefer: tuple[str, ...] = ("upper right", "upper left", "lower right", "lower left"),
    fontsize: int = 9,
    frame: bool = False,
    **legend_kwargs,
):
    """Place a legend in the emptiest corner of the axes.

    Inspects every artist on `ax` (lines, bars, error-bars, scatter, fills),
    samples their occupied pixel bboxes, and picks the corner of the axes that
    has the most empty space for a legend roughly sized to fit the entries.

    Args:
        pad: Fractional inset from the axes edge (data area).
        prefer: Tie-break order among equally-empty corners.
        fontsize: Legend text size.
        frame: Opt-in boxed legend. Default False (frameless). Boxed legends
            are discouraged — prefer frameless or direct labels.
        **legend_kwargs: Forwarded to ax.legend (e.g. title, ncol).

    Returns:
        The matplotlib Legend object.
    """
    fig = ax.get_figure()
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        return ax.legend(loc=prefer[0], fontsize=fontsize, **legend_kwargs)

    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return None

    # Draft legend off-axes to measure its size.
    draft = ax.legend(
        handles,
        labels,
        loc="upper right",
        fontsize=fontsize,
        frameon=frame,
        **legend_kwargs,
    )
    fig.canvas.draw()
    leg_bbox_px = draft.get_window_extent(renderer=renderer)
    leg_w_px = leg_bbox_px.width
    leg_h_px = leg_bbox_px.height
    draft.remove()

    ax_bbox = ax.get_window_extent(renderer=renderer)

    # Gather artist bboxes that count as "data ink" we should avoid.
    artist_bboxes = []
    for art in (
        list(ax.lines)
        + list(ax.patches)
        + list(ax.collections)
        + list(ax.containers)
    ):
        # ErrorbarContainer / BarContainer aren't artists themselves but iterate.
        if hasattr(art, "get_window_extent"):
            try:
                bb = art.get_window_extent(renderer=renderer)
                if bb.width > 0 and bb.height > 0:
                    artist_bboxes.append(bb)
            except Exception:
                pass
        elif hasattr(art, "__iter__"):
            for sub in art:
                try:
                    bb = sub.get_window_extent(renderer=renderer)
                    if bb.width > 0 and bb.height > 0:
                        artist_bboxes.append(bb)
                except Exception:
                    pass

    def overlap_score(corner: str) -> float:
        ax_x, ax_y = _CORNERS[corner]
        # Pixel box for the candidate legend at this corner.
        if ax_x == 1:
            x1 = ax_bbox.x1 - pad * ax_bbox.width
            x0 = x1 - leg_w_px
        else:
            x0 = ax_bbox.x0 + pad * ax_bbox.width
            x1 = x0 + leg_w_px
        if ax_y == 1:
            y1 = ax_bbox.y1 - pad * ax_bbox.height
            y0 = y1 - leg_h_px
        else:
            y0 = ax_bbox.y0 + pad * ax_bbox.height
            y1 = y0 + leg_h_px

        score = 0.0
        for bb in artist_bboxes:
            ox = max(0, min(x1, bb.x1) - max(x0, bb.x0))
            oy = max(0, min(y1, bb.y1) - max(y0, bb.y0))
            score += ox * oy
        return score

    scored = [(overlap_score(c), prefer.index(c), c) for c in prefer]
    scored.sort()  # lowest overlap wins; tie-break by user preference order
    best = scored[0][2]
    if scored[0][0] > 0:
        warnings.warn(
            f"graphs.smart_legend: best corner {best!r} still overlaps "
            "data. Consider tightening axes limits or moving the legend "
            "outside the axes with bbox_to_anchor.",
            stacklevel=2,
        )

    leg = ax.legend(
        handles,
        labels,
        loc=best,
        fontsize=fontsize,
        frameon=frame,
        **legend_kwargs,
    )
    if frame:
        frame_obj = leg.get_frame()
        frame_obj.set_edgecolor(C_SPINE)
        frame_obj.set_linewidth(0.5)
        frame_obj.set_facecolor(_FRAME_FILL)
        frame_obj.set_alpha(0.92)
    return leg


def top_legend(
    fig,
    handles: Sequence,
    labels: Sequence[str],
    *,
    x: float = 0.02,
    y: float | None = None,
    align: str = "left",
    ncol: int | None = None,
    fontsize: float = 7.5,
    handlelength: float = 1.2,
    handletextpad: float = 0.4,
    columnspacing: float = 1.0,
    anchor_to: object | None = None,
    above_axes: float = 0.005,
):
    """Compact frameless legend anchored under the title stack.

    Standard Economist treatment for stacked-bar / thermometer / dumbbell
    charts that share a colour key across panels: a single horizontal row
    of label swatches sitting just below the descriptor block, aligned to
    the ``title_x`` of the chart.

    Args:
        fig: Figure to attach the legend to.
        handles: Legend handles (artists).
        labels: Legend labels matching ``handles``.
        x: Anchor in figure coordinates. With ``align="left"`` this is the
            legend's left edge (match ``finalize(title_x=…)``); with
            ``align="right"`` it is the right edge (use ``bbox.x1`` to flush
            against the chart's right edge).
        y: Top anchor in figure coordinates. When ``None`` (default), the
            legend is placed ``above_axes`` above the top of ``anchor_to``
            (or the first axes in the figure when ``anchor_to`` is None).
        align: ``"left"`` (default) or ``"right"``.
        ncol: Number of columns. Defaults to ``len(handles)`` so each entry
            sits on the same row.
        anchor_to: Axes whose top edge is used for automatic ``y``. Useful
            for chart_top alignment in multi-panel layouts where ``axes[0]``
            isn't the right reference.
        above_axes: Gap (figure coords) between the axes' top and the
            legend's top when ``y`` is auto-computed.
    """
    if align not in ("left", "right"):
        raise ValueError(f"align must be 'left' or 'right', got {align!r}")
    if y is None:
        ref = anchor_to if anchor_to is not None else (fig.axes[0] if fig.axes else None)
        if ref is None:
            y = 0.82
        else:
            fig.canvas.draw()
            y = ref.get_position().y1 + above_axes
    if ncol is None:
        ncol = max(1, len(handles))
    loc = "upper left" if align == "left" else "upper right"
    return fig.legend(
        handles,
        labels,
        loc=loc,
        bbox_to_anchor=(x, y),
        ncol=ncol,
        frameon=False,
        fontsize=fontsize,
        handlelength=handlelength,
        handletextpad=handletextpad,
        columnspacing=columnspacing,
    )
