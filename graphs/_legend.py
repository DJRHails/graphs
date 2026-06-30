"""Smart legend placement — pick the emptiest corner of the axes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from graphs._palette import C_SPINE


@dataclass(frozen=True, kw_only=True)
class TopLegendSpec:
    """Placement parameters of an auto-positioned :func:`top_legend`.

    Stashed on the legend (``legend._graphs_top_legend``) so ``finalize`` can
    reserve a band for it and re-anchor it to the final axes top after
    auto-layout shifts the axes. Only auto-positioned legends (no explicit
    ``y=``) carry one — an explicit ``y`` is a manual override and is never
    moved. The legend's horizontal alignment is already baked into its ``loc``
    at creation, so only the x anchor needs preserving for the re-anchor.

    Attributes:
        x: Horizontal anchor in figure coords (left edge for ``align="left"``,
            right edge for ``align="right"``).
    """

    x: float


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
    prefer: tuple[str, ...] = (
        "upper right",
        "upper left",
        "lower right",
        "lower left",
    ),
    fontsize: int = 9,
    frame: bool = False,
    **legend_kwargs,
):
    """Place a legend in the emptiest corner of the axes, or above it if none is clear.

    Rasterises the actual data "ink" (filled bars/areas mark every cell they cover; thin
    lines / error-bar whiskers / scatter mark only the cells their geometry crosses) onto a coarse
    occupancy grid, then picks the corner whose candidate legend box covers the fewest occupied
    cells. This is faithful where a bounding-box-area score is not — a full-width whisker or a long
    bar no longer ties every corner. When **no** corner is clear of the data, it falls back to a
    frameless :func:`top_legend` above the axes (which reserves its own y-space via ``finalize``)
    rather than dropping the legend on top of the data — so call ``smart_legend`` *before*
    ``finalize`` for the fallback to claim its band.

    Args:
        pad: Fractional inset from the axes edge (data area).
        prefer: Tie-break order among equally-empty corners.
        fontsize: Legend text size.
        frame: Opt-in boxed legend. Default False (frameless). Boxed legends
            are discouraged — prefer frameless or direct labels.
        **legend_kwargs: Forwarded to ax.legend (e.g. title, ncol). Dropped on the
            top-legend fallback, which takes none of the corner-specific options.

    Returns:
        The matplotlib Legend object (a corner legend, or the top-legend fallback).
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

    # Build a coarse occupancy grid of the actual data "ink", then score each corner by how many
    # occupied cells a candidate legend box would cover. This is faithful where summing artist
    # bounding boxes is not: a sparse, wide artist — an errorbar-whisker LineCollection, a long bar
    # series — has a bbox spanning most of the axes, so a bbox-area score ties every corner and
    # collapses the choice to prefer[0] (landing the legend on top of a long bar). Filled patches
    # mark every cell they cover; thin lines / collections mark only the cells their geometry
    # actually crosses, so an empty corner reads as empty even next to a full-width whisker.
    n_cells = 48
    grid_x0, grid_y0 = ax_bbox.x0, ax_bbox.y0
    grid_w = ax_bbox.width or 1.0
    grid_h = ax_bbox.height or 1.0
    occupied: set[tuple[int, int]] = set()

    def _cell(px: float, py: float) -> tuple[int, int]:
        cx = min(n_cells - 1, max(0, int((px - grid_x0) / grid_w * n_cells)))
        cy = min(n_cells - 1, max(0, int((py - grid_y0) / grid_h * n_cells)))
        return cx, cy

    def _mark_filled(bb) -> None:
        cx0, cy0 = _cell(bb.x0, bb.y0)
        cx1, cy1 = _cell(bb.x1, bb.y1)
        for cx in range(min(cx0, cx1), max(cx0, cx1) + 1):
            for cy in range(min(cy0, cy1), max(cy0, cy1) + 1):
                occupied.add((cx, cy))

    def _mark_points(points) -> None:
        for px, py in points:
            occupied.add(_cell(px, py))

    step_px = max(1.0, min(grid_w / n_cells, grid_h / n_cells))

    def _mark_polyline(pixel_pts) -> None:
        # Walk each segment at ~one-cell resolution so a long sparse line marks every cell it
        # crosses, not just its vertices (a 2-point line would otherwise mark only its endpoints).
        pts = [(float(px), float(py)) for px, py in pixel_pts]
        if not pts:
            return
        if len(pts) == 1:
            occupied.add(_cell(*pts[0]))
            return
        for (x0p, y0p), (x1p, y1p) in zip(pts, pts[1:]):
            steps = min(256, max(1, int(max(abs(x1p - x0p), abs(y1p - y0p)) / step_px)))
            for s in range(steps + 1):
                t = s / steps
                occupied.add(_cell(x0p + (x1p - x0p) * t, y0p + (y1p - y0p) * t))

    # Bars / filled areas are solid: mark every cell they cover.
    for patch in ax.patches:
        try:
            bb = patch.get_window_extent(renderer=renderer)
            if bb.width > 0 and bb.height > 0:
                _mark_filled(bb)
        except Exception:
            pass
    # Thin lines: mark every cell the path crosses.
    for line in ax.lines:
        try:
            xy = line.get_xydata()
            if len(xy):
                _mark_polyline(ax.transData.transform(xy))
        except Exception:
            pass
    # Scatter offsets + LineCollection segments (whiskers): thin geometry, not their bbox.
    for col in ax.collections:
        try:
            offsets = col.get_offsets()
            if offsets is not None and len(offsets):
                _mark_points(col.get_offset_transform().transform(offsets))
        except Exception:
            pass
        try:
            for segment in col.get_segments():
                if len(segment):
                    _mark_polyline(ax.transData.transform(segment))
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

        c0x, c0y = _cell(x0, y0)
        c1x, c1y = _cell(x1, y1)
        return float(
            sum(
                (cx, cy) in occupied
                for cx in range(min(c0x, c1x), max(c0x, c1x) + 1)
                for cy in range(min(c0y, c1y), max(c0y, c1y) + 1)
            )
        )

    scored = [(overlap_score(c), prefer.index(c), c) for c in prefer]
    scored.sort()  # lowest overlap wins; tie-break by user preference order
    best = scored[0][2]
    if scored[0][0] > 0:
        # No corner is clear of the data — rather than drop the legend on top of it, anchor a
        # frameless legend above the axes. top_legend stashes a spec that finalize reads to reserve
        # the band (the extra y-space), so this only gains its room when smart_legend is called
        # before finalize (the documented order). Corner-specific legend_kwargs (e.g. a corner loc)
        # don't apply to a top legend and are dropped.
        return top_legend(fig, handles, labels, fontsize=fontsize)

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

    **Hands-off placement.** Call this BEFORE ``finalize`` with no explicit
    ``y=`` (the auto path): the legend is tagged on the figure, and
    ``finalize`` measures its height, reserves a band for it between the
    title stack and the axes, and re-anchors it to the final axes top — so a
    faceted chart with a shared key lays out with no ``subplots_adjust`` and
    no hand-tuned ``y`` / ``y_start`` padding (see
    ``examples/faceted_top_legend.py``). Passing an explicit ``y=`` is a
    manual override: that exact ``y`` is kept and ``finalize`` never moves the
    legend (use it for the call-after-``finalize`` patterns that read the
    finalized axes position directly).

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
    auto_y = y is None
    if auto_y:
        ref = (
            anchor_to if anchor_to is not None else (fig.axes[0] if fig.axes else None)
        )
        if ref is None:
            y = 0.82
        else:
            fig.canvas.draw()
            y = ref.get_position().y1 + above_axes
    if ncol is None:
        ncol = max(1, len(handles))
    loc = "upper left" if align == "left" else "upper right"
    legend = fig.legend(
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
    # Tag an auto-positioned legend so a later ``finalize`` can reserve a band
    # for it under the title stack and re-anchor it to the final axes top. An
    # explicit ``y=`` is a manual override — never tagged, never moved. The tag
    # carries the x anchor ``finalize`` re-applies after auto-layout shifts the
    # axes (the vertical anchor is recomputed from the final axes top).
    if auto_y:
        legend._graphs_top_legend = TopLegendSpec(x=x)
        fig._graphs_top_legend = legend
    return legend
