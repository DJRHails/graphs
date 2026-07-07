"""Chart finalisation — title stack, source line, panel labels."""

import textwrap
import warnings
from dataclasses import dataclass, field

import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms

from graphs._fonts import _get_font, _get_font_condensed
from graphs._links import strip_links
from graphs._palette import C_LABEL_MUTED, C_RED, C_SOURCE, C_SPINE, C_TEXT
from graphs._superscript import _has_marker, render_text_with_superscripts


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


def _draw_rule(fig, tx: float, y_cursor: float) -> None:
    """Draw the short red rule above the title (legacy marker)."""
    rule_w = RULE_WIDTH_PX / (fig.get_figwidth() * fig.dpi)
    fig.add_artist(
        plt.Line2D(
            [tx, tx + rule_w],
            [y_cursor, y_cursor],
            transform=fig.transFigure,
            color=C_RED,
            linewidth=RULE_LINEWIDTH,
            solid_capstyle="butt",
            clip_on=False,
        )
    )


# --- Typography (point sizes) ---
TITLE_SIZE_PT = 12.0
DESCRIPTOR_SIZE_PT = 9.5
SOURCE_SIZE_PT = 9.0
FOOTNOTE_SIZE_PT = SOURCE_SIZE_PT  # footnotes share the source line's size
SOURCE_MEASURE_SIZE_PT = SOURCE_SIZE_PT  # measurement size for footnote packing
PANEL_LABEL_SIZE_PT = 10
Y_AXIS_LABEL_SIZE_PT = 8.5
TICK_LABEL_SIZE_PT = 9

# --- Line heights (line-box multipliers) ---
TITLE_LINESPACING = 1.15
DESCRIPTOR_LINESPACING = 1.20
Y_AXIS_LABEL_LINESPACING = 1.2

# --- Layout gaps (typographic points) ---
DESCRIPTOR_LINE_BOX_PT = 11.4  # DESCRIPTOR_SIZE_PT × DESCRIPTOR_LINESPACING
TITLE_LINE_BOX_PT = 14.0  # TITLE_SIZE_PT × TITLE_LINESPACING
INTER_BLOCK_GAP_PT = 3.5  # gap between title and descriptor blocks
RULE_GAP_PT = 2.0  # gap between title and red rule (marker="rule")
TOP_TICK_CLEARANCE_PT = 6.0  # padding above top-axis tick labels

# --- Marker (delta / favicon triangle) ---
MARKER_SIZE_RATIO = 0.80  # marker_size / title_size
MARKER_GAP_PT = 4.0  # horizontal gap between marker and inline title
RULE_WIDTH_PX = 80  # short red rule width in device pixels
RULE_LINEWIDTH = 3.5  # short red rule stroke width

# --- Tick-pad fallback ---
TICK_PAD_MIN = 4  # default y-tick pad (override if charts ask for more)

# --- Font weights ---
TITLE_WEIGHT = 700  # bold

# --- Panel label ---
PANEL_RULE_WIDTH_PX = 35  # short dark rule width above panel label
PANEL_RULE_LINEWIDTH = 1.2
PANEL_RULE_Y_OFFSET = 0.052  # rule offset above axes top (figure coords)
PANEL_LABEL_Y_OFFSET = 0.010  # label offset above axes top (figure coords)

# --- Source / footnotes vertical positions (figure coords) ---
SOURCE_Y_OFFSET = 0.06  # source line offset below bbox.y0
SOURCE_TICK_CLEARANCE = 0.015  # extra clearance below lowest tick label/xlabel
Y_AXIS_LABEL_MARGIN = 0.005  # y-axis label offset above bbox.y1
FOOTNOTES_LEGACY_Y_OFFSET = 0.045  # legacy notes-only position below base
FOOTNOTES_STACK_GAP = 0.022  # gap when notes wrap above source line
FOOTNOTES_PACK_GAP = 0.02  # horizontal gap between source and inline notes

# --- Auto-layout (subplots_adjust) ---
AUTO_LAYOUT_LEFT = 0.02  # default left margin set by finalize's auto-layout
AUTO_LAYOUT_RIGHT = 0.96  # default right margin
AUTO_LAYOUT_TOP_PAD_PT = 6.0  # breathing room above the title-stack
AUTO_LAYOUT_BOTTOM_MARGIN = 0.020  # breathing room below the source baseline
AUTO_LAYOUT_TICK_RESERVE_PT = 16.0  # reserve for a single row of x-tick labels
AUTO_LAYOUT_MARKER_RESERVE_PT = 2.0  # marker overhang above title cap-height
AUTO_LAYOUT_SIDE_GUTTER_PT = 4.0  # gutter between a measured side label and the edge
AUTO_LAYOUT_WSPACE_GUTTER_PT = 10.0  # gutter added to inter-column label width
AUTO_LAYOUT_PANEL_LABEL_PT = 22.0  # rule + bold panel_label height between rows
AUTO_LAYOUT_HSPACE_GUTTER_PT = 6.0  # breathing room between stacked-row bands
AUTO_LAYOUT_TOP_LEGEND_GAP_PT = 5.0  # gap above an auto top_legend (legend↔descriptor)
AUTO_LAYOUT_Y_AXIS_LABEL_GAP_PT = 4.0  # gap above a y_axis_label (label↔descriptor)


# Favicon triangle geometry (hails.info/favicon.svg) — outer red outline,
# inner hollow cut-out. Both triangles are concentric (same centroid). Outer
# base spans (0,0)-(1,0) with apex at (0.5, _TRI_H). True equilateral height
# is √3/2 ≈ 0.866; the favicon shape is slightly taller than equilateral, so
# we scale by _TRI_SKEW (>1 = isoceles taller, =1 = perfect equilateral).
_TRI_SKEW = 1.05  # 1.0 = equilateral, 1.05 ≈ 5% taller (favicon-like)
_TRI_H = (3**0.5 / 2) * _TRI_SKEW
_TRI_OUTER = (
    (0.5, _TRI_H),  # top apex
    (0.0, 0.0),  # bottom-left
    (1.0, 0.0),  # bottom-right
)
_INNER_SCALE = 0.35
_INNER_LIFT = _TRI_H * (1 - _INNER_SCALE) / 3  # centroids coincide
_TRI_INNER = (
    (0.5, _INNER_LIFT + _INNER_SCALE * _TRI_H),  # top apex
    (0.5 - _INNER_SCALE / 2, _INNER_LIFT),  # bottom-left
    (0.5 + _INNER_SCALE / 2, _INNER_LIFT),  # bottom-right
)


def _draw_logo_triangle(
    fig,
    tx: float,
    y_cursor: float,
    *,
    color: str = C_RED,
    size_pt: float = 13.0,
) -> None:
    """Draw the hails.info favicon triangle as a vector hollow marker.

    The triangle is anchored with its bottom-left at ``(tx, y_cursor)`` in
    figure coordinates so it aligns the same way as the legacy Δ glyph or
    short rule (both bottom-anchored). ``size_pt`` controls the visual
    height in typographic points so the marker scales consistently with
    the surrounding title typography.

    Renders as a single ``PathPatch`` with two sub-paths and even-odd fill
    rule — the outer triangle is filled with ``color`` and the inner
    triangle punches a transparent hole through it. Stays vector at
    savefig time.
    """
    fig_w_in = fig.get_figwidth()
    fig_h_in = fig.get_figheight()
    # Convert size from points → figure-relative units on each axis. The
    # vertex table is bbox-normalised so vy=1 equals the full triangle
    # height; size_pt therefore equals the visual height in typographic
    # points. Width is scaled by the favicon's bbox aspect ratio so the
    # rendered triangle keeps its near-equilateral proportions regardless
    # of figure aspect.
    size_h = size_pt / 72.0 / fig_h_in
    size_w = size_h * (fig_h_in / fig_w_in)

    def _to_fig(verts):
        return [(tx + vx * size_w, y_cursor + vy * size_h) for vx, vy in verts]

    Path = mpath.Path
    outer = _to_fig(_TRI_OUTER)
    # Reverse the inner triangle's winding so matplotlib's default non-zero
    # winding fill rule treats it as a hole (the two sub-paths have opposite
    # orientations, so they cancel where they overlap).
    inner = _to_fig(tuple(reversed(_TRI_INNER)))
    verts = [
        outer[0],
        outer[1],
        outer[2],
        outer[0],
        inner[0],
        inner[1],
        inner[2],
        inner[0],
    ]
    codes = [
        Path.MOVETO,
        Path.LINETO,
        Path.LINETO,
        Path.CLOSEPOLY,
        Path.MOVETO,
        Path.LINETO,
        Path.LINETO,
        Path.CLOSEPOLY,
    ]
    patch = mpatches.PathPatch(
        Path(verts, codes),
        transform=fig.transFigure,
        facecolor=color,
        edgecolor="none",
        linewidth=0,
        clip_on=False,
    )
    fig.add_artist(patch)


def _draw_delta(fig, tx: float, y_cursor: float) -> None:
    """Draw the hails.info hollow red triangle above the title (default marker)."""
    _draw_logo_triangle(fig, tx, y_cursor)


def _xtick_band_height_fig(fig, ax) -> float | None:
    """Measure the bottom x-tick labels' rendered height in figure fraction.

    Returns the vertical extent the *bottom* x-axis tick labels occupy below
    the axes baseline (``bbox.y0``), expressed as a fraction of the figure
    height. Categorical bar charts put category names here (``forced`` /
    ``calibrated`` / …); the auto-layout must reserve this band so a
    ``footnotes()``/source line drawn below it can't overlap the labels.

    Mirrors the renderer-based measurement the title-stack and source-line
    placement already use (``get_window_extent`` transformed through
    ``transFigure``). Tick labels that sit *above* the axes (``bar_h`` /
    ``x_axis_top`` / a ``secondary_xaxis("top")``) are ignored — those are
    handled by the top-stack clearance, not the bottom band.

    Returns:
        The band height as a figure fraction. ``0.0`` when there are no
        visible bottom labels (line/scatter charts, top-mounted ticks) — the
        caller then reserves nothing extra, so those charts are unaffected.
        ``None`` when the renderer is unavailable after a draw attempt
        (non-Agg backend), signalling the caller to fall back to a fixed
        reserve since the labels couldn't be measured.
    """
    try:
        renderer = fig.canvas.get_renderer()
    except AttributeError:
        fig.canvas.draw()
        try:
            renderer = fig.canvas.get_renderer()
        except AttributeError:
            return None

    baseline_y0 = ax.get_position().y0
    inv = fig.transFigure.inverted()
    lowest_y0 = baseline_y0
    for tl in ax.get_xticklabels():
        if not tl.get_text() or not tl.get_visible():
            continue
        tl_bb = tl.get_window_extent(renderer=renderer).transformed(inv)
        # Skip labels mounted above the axes (bar_h / x_axis_top); only the
        # band below the baseline competes with the footnote/source line.
        if tl_bb.y0 >= baseline_y0:
            continue
        lowest_y0 = min(lowest_y0, tl_bb.y0)
    return max(0.0, baseline_y0 - lowest_y0)


def _get_renderer(fig):
    """Return the figure's Agg renderer, drawing once if it isn't realised yet.

    Mirrors the no-renderer-yet handling the title-stack and x-tick
    measurements already use. Returns ``None`` on a backend that can't hand
    back a renderer even after a draw (non-Agg) so callers fall back to fixed
    constants instead of guessing.
    """
    try:
        return fig.canvas.get_renderer()
    except AttributeError:
        fig.canvas.draw()
        try:
            return fig.canvas.get_renderer()
        except AttributeError:
            return None


def _top_legend(fig):
    """Return the auto-positioned :func:`top_legend` tagged on ``fig``, or None.

    ``top_legend`` stashes an auto-positioned legend (no explicit ``y=``) at
    ``fig._graphs_top_legend`` so ``finalize`` can reserve a band for it and
    re-anchor it. Returns ``None`` when no such legend exists (the common case —
    most charts have no top legend) or when the tagged legend was since removed.
    """
    legend = getattr(fig, "_graphs_top_legend", None)
    if legend is None:
        return None
    if legend not in getattr(fig, "legends", []):
        return None  # removed since tagging
    return legend


def _top_legend_height_fig(fig, legend) -> float | None:
    """Measure ``legend``'s rendered height as a fraction of the figure height.

    Mirrors the renderer-based measurement the title-stack and x-tick code use
    (``get_window_extent`` through ``transFigure``). Returns ``None`` when the
    renderer is unavailable (non-Agg backend) so the caller falls back to
    reserving nothing extra rather than guessing.
    """
    renderer = _get_renderer(fig)
    if renderer is None:
        return None
    try:
        bb = legend.get_window_extent(renderer=renderer)
    except Exception:
        return None
    if bb.height <= 0:
        return 0.0
    return bb.transformed(fig.transFigure.inverted()).height


@dataclass(kw_only=True)
class _YAxisLabelSpec:
    """Placement record of one :func:`y_axis_label` block, tagged on the figure.

    ``y_axis_label`` renders against the axes position at call time; when
    ``finalize`` then auto-lays-out the margins the axes moves and the label is
    left stranded — colliding with the title stack when the stack is tall (the
    touchstone ``length_control_guilt_vs_n`` failure). Each call appends a spec
    to ``fig._graphs_y_axis_labels`` so ``finalize`` can (a) reserve a band for
    the label between the descriptor and the axes top and (b) re-anchor the
    rendered artists to the final axes position. Labels rendered *after*
    ``finalize`` keep their spec too, but nothing reads it — they stay where
    they were drawn (the manual-placement path).

    Attributes:
        ax: The axes the label titles (its top edge is the anchor).
        artists: Every ``Text`` artist the label rendered (the wrapped text
            block plus the optional unit line — and each superscript chunk when
            markers split the render).
        axes_top: ``ax.get_position().y1`` when the label was rendered.
        anchor_x: The x edge the label is flush against at render time
            (``bbox.x1`` for ``side="right"``, ``bbox.x0`` for ``"left"``).
        side: ``"right"`` or ``"left"`` — which axes edge ``anchor_x`` tracks.
    """

    ax: object
    artists: list = field(default_factory=list)
    axes_top: float = 0.0
    anchor_x: float = 0.0
    side: str = "right"


def _y_axis_label_specs(fig) -> list[_YAxisLabelSpec]:
    """Live :class:`_YAxisLabelSpec` records tagged on ``fig``.

    Filters out stale specs whose artists have since been removed from the
    figure, so a caller that cleared its texts doesn't get phantom bands.
    """
    specs = getattr(fig, "_graphs_y_axis_labels", [])
    fig_texts = set(fig.texts)
    return [s for s in specs if any(a in fig_texts for a in s.artists)]


def _y_axis_label_band_fig(fig, specs: list[_YAxisLabelSpec]) -> float:
    """Height of the tallest ``y_axis_label`` block, in figure fraction.

    Measures the union of each spec's rendered artists with the renderer
    (mirroring the title-stack / top-legend measurements) and returns the
    tallest block plus its ``Y_AXIS_LABEL_MARGIN`` seat above the axes top.
    Returns ``0.0`` when nothing measures (no specs, or a non-Agg backend) —
    the caller then reserves nothing, today's behaviour.
    """
    renderer = _get_renderer(fig)
    if renderer is None:
        return 0.0
    inv = fig.transFigure.inverted()
    band = 0.0
    for spec in specs:
        top: float | None = None
        bottom: float | None = None
        for artist in spec.artists:
            try:
                bb = artist.get_window_extent(renderer=renderer).transformed(inv)
            except Exception:
                continue
            top = bb.y1 if top is None else max(top, bb.y1)
            bottom = bb.y0 if bottom is None else min(bottom, bb.y0)
        if top is None or bottom is None:
            continue
        band = max(band, (top - bottom) + Y_AXIS_LABEL_MARGIN)
    return band


def _reanchor_y_axis_labels(fig) -> None:
    """Shift each ``y_axis_label`` block to its axes' final position.

    The label artists were rendered flush against the axes edge *before*
    ``finalize`` moved it; shift every artist by the axes-edge delta so the
    block seats just above the final axes top again (the reserved band above it
    keeps the title stack clear). Pure translation in figure coords — the
    per-chunk superscript layout inside the block is preserved. Updates each
    spec's stored anchors so a repeated ``finalize`` is a no-op shift.
    """
    for spec in _y_axis_label_specs(fig):
        pos = spec.ax.get_position()
        new_anchor_x = pos.x1 if spec.side == "right" else pos.x0
        dx = new_anchor_x - spec.anchor_x
        dy = pos.y1 - spec.axes_top
        if abs(dx) < 1e-12 and abs(dy) < 1e-12:
            continue
        for artist in spec.artists:
            x_old, y_old = artist.get_position()
            artist.set_position((x_old + dx, y_old + dy))
        spec.anchor_x = new_anchor_x
        spec.axes_top = pos.y1


def _side_protrusions_fig(fig, ax) -> tuple[float, float] | None:
    """Measure how far axis-side text spills past ``ax``'s left/right edges.

    Returns ``(left, right)`` figure-fractions: the left value is how far the
    text on the left of the axes extends *to the left of* ``ax.x0`` (0.0 when
    nothing protrudes), the right value how far the text on the right extends
    *to the right of* ``ax.x1``. Measured artists are the y-tick labels, the
    in-axes ``ax.yaxis.label``, and end-of-line direct labels (``label_lines``,
    when run before ``finalize``).

    Only *horizontally shift-invariant* text is measured: a y-tick label's gap
    to the axis edge is fixed in *points* (the tick ``pad``), so it doesn't
    change when ``subplots_adjust`` shifts the axes — measuring the protrusion
    once and reserving it is exact, no iteration. (x-tick labels are excluded:
    their horizontal reach depends on the data-to-axes mapping, which the margin
    shift itself changes, so they aren't a stable basis for the margin.)

    Returns ``None`` when the renderer is unavailable (non-Agg backend), so
    the caller keeps today's fixed side margins.
    """
    renderer = _get_renderer(fig)
    if renderer is None:
        return None

    inv = fig.transFigure.inverted()
    pos = ax.get_position()
    left = 0.0
    right = 0.0

    artists = list(ax.get_yticklabels())
    if ax.yaxis.label.get_text():
        artists.append(ax.yaxis.label)
    # End-of-line direct labels (label_lines) sit to the right of the data,
    # often past x1; in-chart annotations stay inside the box and don't count.
    artists.extend(ax.texts)

    for art in artists:
        if not art.get_visible() or not (getattr(art, "get_text", lambda: "")()):
            continue
        try:
            bb = art.get_window_extent(renderer=renderer).transformed(inv)
        except Exception:
            continue
        if bb.width <= 0:
            continue
        left = max(left, pos.x0 - bb.x0)
        right = max(right, bb.x1 - pos.x1)
    return max(0.0, left), max(0.0, right)


def _xtick_side_spill(fig) -> tuple[float, float] | None:
    """Measure outer x-tick labels that spill past the figure's left/right edges.

    The leftmost column's leftmost x-tick (and the rightmost column's rightmost)
    is centred on its data position, so half of it can hang past the panel edge
    and off the figure. Unlike y-tick protrusion this is *not* shift-invariant
    (it tracks the axes width), so it's measured AFTER the main margins are set
    and corrected in a single bounded pass. Only ticks whose mark sits *inside*
    the panel's x-span count — autoscale-margin ticks that fall outside the data
    box aren't drawn against the spine and shouldn't drive the margin. Returns
    ``(left_spill, right_spill)`` as figure-fractions below 0 / above 1, or
    ``None`` (non-Agg).
    """
    renderer = _get_renderer(fig)
    if renderer is None:
        return None
    inv = fig.transFigure.inverted()
    columns = _gridspec_columns(fig)
    outer = (
        [columns[min(columns)], columns[max(columns)]]
        if columns
        else [fig.axes, fig.axes]
    )

    def _edge_spills(axes_list, *, side: str) -> float:
        spill = 0.0
        for axes in axes_list:
            x_lo, x_hi = axes.get_xlim()
            for tick, tl in zip(axes.get_xticks(), axes.get_xticklabels()):
                if not tl.get_text() or not tl.get_visible():
                    continue
                if not (x_lo <= tick <= x_hi):
                    continue  # tick mark is off the data box; not against a spine
                bb = tl.get_window_extent(renderer=renderer).transformed(inv)
                spill = max(spill, -bb.x0 if side == "left" else bb.x1 - 1.0)
        return spill

    return max(0.0, _edge_spills(outer[0], side="left")), max(
        0.0, _edge_spills(outer[1], side="right")
    )


def _gridspec_columns(fig):
    """Group ``fig.axes`` by gridspec column index → list of axes in that column.

    Only axes laid out through a shared :class:`~matplotlib.gridspec.GridSpec`
    (the ``subplots``/``subplots_adjust`` family) are grouped; inset axes added
    via ``fig.add_axes`` carry no subplotspec and are skipped. Returns an
    ordered ``{col_index: [axes, …]}`` mapping (empty when nothing is on a
    gridspec).
    """
    columns: dict[int, list] = {}
    for axes in fig.axes:
        spec = axes.get_subplotspec()
        if spec is None:
            continue
        col = spec.colspan.start
        columns.setdefault(col, []).append(axes)
    return dict(sorted(columns.items()))


def _gridspec_shape(fig) -> tuple[int, int]:
    """Return the ``(nrows, ncols)`` of the figure's primary gridspec.

    Reads the geometry off the first axes that carries a subplotspec; returns
    ``(1, 1)`` when no axes is on a gridspec (a lone ``add_axes`` figure).
    """
    for axes in fig.axes:
        spec = axes.get_subplotspec()
        if spec is None:
            continue
        gs = spec.get_gridspec()
        return gs.nrows, gs.ncols
    return 1, 1


def _compute_wspace(fig) -> float | None:
    """Inter-column ``wspace`` so neighbouring panels' y-labels don't collide.

    ``wspace`` is matplotlib's inter-column gap expressed as a fraction of the
    *average axes width*. The physical gap a column boundary must hold is the
    right-side y-tick/label protrusion of the left panel plus the left-side
    protrusion of the right panel (plus a small gutter). Independent-y panels
    (each carrying its own labelled axis, e.g. ``right_axis`` per panel) need a
    wide gap; shared-y panels (only the outer axis labelled) need almost none.

    Returns the ``wspace`` fraction, or ``None`` when there's a single column or
    the renderer can't measure (non-Agg) — the caller then leaves ``wspace``
    untouched.
    """
    columns = _gridspec_columns(fig)
    if len(columns) < 2:
        return None

    fig_w_in = fig.get_figwidth()
    pt2fig_w = 1.0 / 72.0 / fig_w_in
    gutter = AUTO_LAYOUT_WSPACE_GUTTER_PT * pt2fig_w

    col_items = list(columns.items())
    max_gap = 0.0
    avg_w = 0.0
    n_axes = 0
    for _, axes_list in col_items:
        for axes in axes_list:
            avg_w += axes.get_position().width
            n_axes += 1
    if n_axes == 0:
        return None
    avg_w /= n_axes

    # Pair adjacent columns: left column's right protrusion + right column's
    # left protrusion must fit in the boundary between them.
    for (_, left_axes), (_, right_axes) in zip(col_items, col_items[1:]):
        right_of_left = 0.0
        for axes in left_axes:
            measured = _side_protrusions_fig(fig, axes)
            if measured is not None:
                right_of_left = max(right_of_left, measured[1])
        left_of_right = 0.0
        for axes in right_axes:
            measured = _side_protrusions_fig(fig, axes)
            if measured is not None:
                left_of_right = max(left_of_right, measured[0])
        max_gap = max(max_gap, right_of_left + left_of_right + gutter)

    if avg_w <= 0:
        return None
    return max_gap / avg_w


def _compute_hspace(fig, *, has_panel_labels: bool) -> float | None:
    """Inter-row ``hspace`` so a row's x-ticks (and panel label) clear the next.

    ``hspace`` is matplotlib's inter-row gap as a fraction of the *average axes
    height*. A row boundary must hold the upper row's bottom x-tick band plus,
    when panels carry ``panel_label`` headings, the rule-and-label height that
    sits above the lower row. Returns ``None`` for a single row or a non-Agg
    backend (caller leaves ``hspace`` untouched).
    """
    nrows, _ = _gridspec_shape(fig)
    if nrows < 2:
        return None

    fig_h_in = fig.get_figheight()
    pt2fig_h = 1.0 / 72.0 / fig_h_in

    band = 0.0
    avg_h = 0.0
    n_axes = 0
    for axes in fig.axes:
        if axes.get_subplotspec() is None:
            continue
        avg_h += axes.get_position().height
        n_axes += 1
        measured = _xtick_band_height_fig(fig, axes)
        if measured is not None:
            band = max(band, measured)
    if n_axes == 0 or avg_h <= 0:
        return None
    avg_h /= n_axes

    gap = band + AUTO_LAYOUT_HSPACE_GUTTER_PT * pt2fig_h
    if has_panel_labels:
        gap += AUTO_LAYOUT_PANEL_LABEL_PT * pt2fig_h
    return gap / avg_h


def _lowest_row_axes(fig) -> list:
    """Return the gridspec axes on the bottom row (highest ``rowspan.stop``).

    The bottom margin of a multi-row grid must clear the *lowest* row's x-tick
    band, not the row ``finalize`` was anchored on (usually the top). Returns
    ``[]`` when no axes is on a gridspec.
    """
    rows: dict[int, list] = {}
    for axes in fig.axes:
        spec = axes.get_subplotspec()
        if spec is None:
            continue
        rows.setdefault(spec.rowspan.stop, []).append(axes)
    if not rows:
        return []
    return rows[max(rows)]


def _compute_side_margins(fig) -> tuple[float, float]:
    """Compute ``(left, right)`` figure-fraction margins from the y-axis text.

    Reserves the *outer* sides of the whole figure: the left margin holds the
    leftmost column's left-protruding y-axis text (long category labels on a
    horizontal bar / heatmap row, a left-mounted ``y_axis_label``), the right
    margin holds the rightmost column's right-protruding text (right-axis
    numeric labels, end-of-line ``label_lines``). A side with nothing
    protruding keeps the small default (``AUTO_LAYOUT_LEFT`` /
    ``1 - AUTO_LAYOUT_RIGHT``), so a plain right-axis line chart is unchanged
    on the left.

    The label-to-axis-edge gap is fixed in points (the tick ``pad``), so it is
    invariant under the horizontal shift ``subplots_adjust`` then applies —
    measuring the protrusion once and reserving it is exact.

    Falls back to the fixed ``(AUTO_LAYOUT_LEFT, AUTO_LAYOUT_RIGHT)`` when the
    renderer can't measure (non-Agg backend).
    """
    default_left = AUTO_LAYOUT_LEFT
    default_right = AUTO_LAYOUT_RIGHT

    fig_w_in = fig.get_figwidth()
    gutter = AUTO_LAYOUT_SIDE_GUTTER_PT / 72.0 / fig_w_in

    columns = _gridspec_columns(fig)
    measured_any = False
    left_protrusion = 0.0
    right_protrusion = 0.0

    if columns:
        # Grid: reserve the outer sides only — leftmost column's left protrusion
        # and rightmost column's right protrusion (inter-column gaps are wspace).
        col_items = list(columns.items())
        left_axes, right_axes = col_items[0][1], col_items[-1][1]
    else:
        # Single column (one axes, or a 1-col grid): each axes contributes both
        # sides.
        left_axes = right_axes = list(fig.axes)

    for axes in left_axes:
        measured = _side_protrusions_fig(fig, axes)
        if measured is not None:
            measured_any = True
            left_protrusion = max(left_protrusion, measured[0])
    for axes in right_axes:
        measured = _side_protrusions_fig(fig, axes)
        if measured is not None:
            measured_any = True
            right_protrusion = max(right_protrusion, measured[1])

    if not measured_any:
        return default_left, default_right

    left = max(default_left, left_protrusion + gutter)
    right = min(default_right, 1.0 - (right_protrusion + gutter))
    return left, right


def _ensure_bottom_clearance(fig, *, depth_below_panels: float) -> bool:
    """Raise the panels so a band ``depth_below_panels`` deep stays on-figure.

    ``footnotes`` draws the source/notes band below the lowest panel's x-tick
    labels; on a faceted figure (or one that draws its source via ``footnotes``
    rather than ``finalize``) the band can fall off the bottom because
    ``finalize`` — told ``source=""`` — reserved no source room. This grows the
    figure's bottom margin (which only moves the lower axes edge up, leaving the
    axes *top* and anything anchored to it untouched) so the band's lowest point
    lands at ``AUTO_LAYOUT_BOTTOM_MARGIN`` above the figure floor.

    ``depth_below_panels`` is the band's full reach below the lowest panel
    baseline (x-tick band + source offset + block height). Returns ``True`` and
    redraws when it grew the margin, ``False`` when the current margin already
    cleared the band (so callers skip the redraw).

    Skips multi-row grids: there, growing the bottom margin moves the lower
    row's *top* (a fraction of the redistributed height), which would detach an
    already-drawn ``panel_label`` — so ``finalize`` reserves their source band
    up front instead and this stays a no-op.
    """
    nrows, _ = _gridspec_shape(fig)
    if nrows > 1:
        return False
    panel_y0s = [
        a.get_position().y0 for a in fig.axes if a.get_subplotspec() is not None
    ]
    if not panel_y0s:
        return False
    lowest_panel_y0 = min(panel_y0s)

    needed_y0 = depth_below_panels + AUTO_LAYOUT_BOTTOM_MARGIN
    if lowest_panel_y0 >= needed_y0 - 1e-6:
        return False

    # Grow the bottom margin by the shortfall. subplots_adjust(bottom=) keeps
    # the axes top fixed, so the title stack / panel labels stay put.
    grow = needed_y0 - lowest_panel_y0
    fig.subplots_adjust(bottom=fig.subplotpars.bottom + grow)
    fig.canvas.draw()
    return True


def _estimate_note_rows(fig, notes: tuple[str, ...]) -> int:
    """Worst-case wrapped row count for the note block (notes stacked above the source).

    Mirrors ``footnotes()``'s own wrap: measure the single-line width, derive a per-character
    pitch, and word-wrap to ~full figure width — the width notes get when they stack above the
    source line. This lets the band reserve the *exact* depth a multi-line footnote needs, so the
    caller never has to hand-pass ``footnote_lines``. Returns ``1`` if it cannot measure (no
    renderer yet) — the historical single-row reservation.
    """
    notes_clean, _ = strip_links("  ".join(notes))
    if not notes_clean:
        return 1
    try:
        fp = fm.FontProperties(family=_get_font_condensed(), weight="light")
        probe = fig.text(
            0, 0, notes_clean, fontproperties=fp, fontsize=FOOTNOTE_SIZE_PT
        )
        bb = probe.get_window_extent(renderer=fig.canvas.get_renderer())
        text_w = bb.width / (fig.get_figwidth() * fig.dpi)
        probe.remove()
    except Exception:
        return 1
    # max_width_frac (0.95) minus the x anchor (0.02): the width notes wrap to above the source.
    avail_frac = 0.93
    per_char = text_w / len(notes_clean) if notes_clean else 0.0
    max_chars = int(avail_frac / per_char) if per_char > 0 else len(notes_clean)
    return _wrap_preserve_offsets(notes_clean, max_chars).count("\n") + 1


def _footnotes_band_depth(fig, notes: tuple[str, ...], source: str | None) -> float:
    """Reach below the lowest panel baseline of the source/notes band.

    The band sits an x-tick band plus ``SOURCE_Y_OFFSET`` below the baseline, then the source line
    itself, plus one line box per note row that wraps above the source. The wrapped row count is
    measured from the actual note text (:func:`_estimate_note_rows`), so a 2- or 3-line footnote
    reserves its full depth automatically — callers do not pass ``footnote_lines``. Returns a
    figure-fraction depth.
    """
    fig_h_in = fig.get_figheight()
    pt2fig = 1.0 / 72.0 / fig_h_in

    band = 0.0
    for a in fig.axes:
        if a.get_subplotspec() is None:
            continue
        measured = _xtick_band_height_fig(fig, a)
        if measured is not None:
            band = max(band, measured)

    depth = band + SOURCE_Y_OFFSET + SOURCE_SIZE_PT * 1.2 * pt2fig
    if notes:
        # Notes that can't pack on the source row wrap above it — reserve a line box per wrapped
        # row (measured, not a conservative single row) plus the stack gap so the block clears.
        depth += (
            FOOTNOTES_STACK_GAP
            + FOOTNOTE_SIZE_PT * 1.2 * pt2fig * _estimate_note_rows(fig, notes)
        )
    return depth


def _compute_auto_pads(
    fig,
    ax,
    *,
    title: str,
    descriptor: str,
    source: str,
    marker: str,
    y_start: float,
    footnote_lines: int,
    top_legend_band: float = 0.0,
    top_panel_label_band: float = 0.0,
    y_axis_label_band: float = 0.0,
) -> tuple[float, float]:
    """Compute (top_pad, bottom_pad) for ``fig.subplots_adjust``.

    Top pad reserves room for the title-stack drawn in figure coords
    above ``bbox.y1`` (descriptor lines, gap, title lines, marker
    overhang, ``y_start`` padding, plus a small breathing margin). When an
    auto-positioned ``top_legend`` is present, ``top_legend_band`` (its measured
    height plus a gap, in figure fraction) is added so the title-stack drops
    enough to clear the legend row that sits between it and the axes. When the
    top row carries ``panel_label`` headings (``top_panel_label_band`` > 0, set
    by ``panel_labels=True``), that band is reserved too so the rule-and-label
    heading — which ``panel_label`` draws *above* the axes top — sits in the top
    margin rather than colliding with the axes or an overlying top legend.
    ``y_axis_label_band`` (measured block height plus a gap) reserves the strip
    a pre-``finalize`` :func:`y_axis_label` occupies just above the axes top, so
    the descriptor seats above the label instead of on it.

    Bottom pad reserves room for the source line at its true depth below the
    axes baseline, ``max(SOURCE_Y_OFFSET, tick_band + SOURCE_TICK_CLEARANCE)``,
    where ``tick_band`` is the *measured* height of the bottom x-tick labels
    (``_xtick_band_height_fig`` — zero when there are none, so line/scatter
    charts are unaffected). Short numeric ticks leave the ``SOURCE_Y_OFFSET``
    term winning (charts unchanged); tall category labels make the tick term
    win, lifting the source clear of them. Extra ``footnotes()`` rows that
    stack above the source deepen the reservation further, so a categorical
    chart with multi-line footnotes no longer collides its category labels
    with the first footnote row. A breathing margin is added below.
    """
    fig_h_in = fig.get_figheight()
    pt2fig = 1.0 / 72.0 / fig_h_in

    title_block_pt = 0.0
    if title:
        n_title_lines = title.count("\n") + 1
        title_block_pt += TITLE_LINE_BOX_PT * n_title_lines

    desc_block_pt = 0.0
    if descriptor:
        n_desc_lines = descriptor.count("\n") + 1
        desc_block_pt += DESCRIPTOR_LINE_BOX_PT * n_desc_lines

    gap_pt = INTER_BLOCK_GAP_PT if (title and descriptor) else 0.0

    marker_pt = 0.0
    if marker == "delta" and not title:
        # Standalone delta sits at y_cursor and rises one marker height.
        marker_pt = TITLE_SIZE_PT * MARKER_SIZE_RATIO
    elif marker == "rule":
        # Rule sits above the title with a small gap.
        marker_pt = RULE_GAP_PT + 2.0
    elif marker == "delta" and title:
        # Inline marker apex can extend slightly above title cap-height.
        marker_pt = AUTO_LAYOUT_MARKER_RESERVE_PT

    stack_pt = title_block_pt + desc_block_pt + gap_pt + marker_pt
    top_pad = (
        y_start
        + top_legend_band
        + top_panel_label_band
        + y_axis_label_band
        + stack_pt * pt2fig
        + AUTO_LAYOUT_TOP_PAD_PT * pt2fig
    )

    # Reserve the measured height of the bottom x-tick labels (category names
    # on a vertical bar chart). A measured 0.0 means there are genuinely no
    # bottom labels (line/scatter charts, top-mounted ticks) — reserve nothing
    # so those charts are unaffected. Only fall back to the fixed single-row
    # reserve when the renderer couldn't measure at all (``None``, non-Agg).
    #
    # On a multi-row grid the bottom margin governs the *lowest* row's baseline,
    # so measure that row's x-tick band, not the (usually top) anchor row's.
    band_axes = _lowest_row_axes(fig) or [ax]
    measured_bands = [_xtick_band_height_fig(fig, a) for a in band_axes]
    if all(b is None for b in measured_bands):
        tick_band = AUTO_LAYOUT_TICK_RESERVE_PT * pt2fig
    else:
        tick_band = max(b for b in measured_bands if b is not None)

    # Facets draw their source via a later ``footnotes(fig, source=…)`` call, so
    # ``finalize`` is told ``source=""`` and would reserve no source room — yet
    # a multi-row grid can't fix that after the fact (growing the bottom there
    # moves the lower row's *top*, detaching its panel label). Reserve the
    # source band up front whenever the figure is a multi-row grid, using the
    # additive depth ``footnotes`` actually places at (tick band + offset +
    # line), not finalize's own ``max(...)`` placement.
    nrows, _ = _gridspec_shape(fig)
    source_h_fig = SOURCE_SIZE_PT * pt2fig
    footnotes_source = nrows > 1 and not source and footnote_lines == 0
    if footnotes_source:
        return top_pad, _footnotes_band_depth(
            fig, (), "src"
        ) + AUTO_LAYOUT_BOTTOM_MARGIN

    has_source_band = bool(source) or footnote_lines > 0
    if not has_source_band:
        return top_pad, tick_band + AUTO_LAYOUT_BOTTOM_MARGIN

    # The source line is placed below the lowest of ``bbox.y0 - SOURCE_Y_OFFSET``
    # and ``(bbox.y0 - tick_band) - SOURCE_TICK_CLEARANCE`` (see the source
    # placement in ``finalize`` and ``footnotes``), i.e. its depth below the
    # axes baseline is ``max(SOURCE_Y_OFFSET, tick_band + SOURCE_TICK_CLEARANCE)``.
    # For short numeric ticks the ``SOURCE_Y_OFFSET`` term wins (so line/scatter
    # charts are unchanged); for tall category labels the tick term wins, lifting
    # the source clear of the labels.
    source_depth = max(SOURCE_Y_OFFSET, tick_band + SOURCE_TICK_CLEARANCE)

    # Extra footnote rows stack ABOVE the source line. When they do,
    # ``footnotes()`` drops the source baseline by the stack height so the whole
    # block clears the tick labels — reserve that matching depth: the tick band,
    # the clearance, the stack gap, and one footnote line box per row.
    extra_line = max(FOOTNOTES_STACK_GAP, FOOTNOTE_SIZE_PT * 1.2 * pt2fig)
    if footnote_lines > 0:
        wrap_depth = (
            tick_band
            + SOURCE_TICK_CLEARANCE
            + FOOTNOTES_STACK_GAP
            + extra_line * footnote_lines
        )
        source_depth = max(source_depth, wrap_depth)

    bottom_pad = source_depth + source_h_fig + AUTO_LAYOUT_BOTTOM_MARGIN

    return top_pad, bottom_pad


def _superscript_axis_label(ax, axis: str) -> None:
    """Re-render an axis label through ``render_text_with_superscripts``.

    Standard ``ax.set_xlabel`` / ``ax.set_ylabel`` calls produce a single
    matplotlib ``Text`` artist that renders footnote markers (``*``, ``†``,
    ``‡``, ``§``) inline at full size. This helper detects markers, hides
    the original artist, and re-renders the same string at the same anchor
    in figure coordinates so the markers come out as proper superscripts.

    Only labels containing a marker are touched; plain labels keep their
    original matplotlib artist (and any styling matplotlib applies via
    rcParams or the user's ``set_xlabel(..., rotation=...)`` call).

    Limitations:
      * Rotation other than 0 is not preserved — the re-rendered text uses
        the default horizontal orientation. Charts that rotate axis labels
        AND use footnote markers will need to call
        ``render_text_with_superscripts`` directly.
      * Only the axes passed to ``finalize`` is processed. Faceted layouts
        that share an xlabel on a single subplot are fine; charts that set
        per-subplot xlabels with markers need one ``finalize`` call per
        subplot.
    """
    label_artist = ax.xaxis.label if axis == "x" else ax.yaxis.label
    text = label_artist.get_text()
    if not text or not _has_marker(text):
        return

    fig = ax.get_figure()
    fig.canvas.draw()

    color = label_artist.get_color()
    fontsize = label_artist.get_fontsize()
    fp = label_artist.get_fontproperties()
    ha = label_artist.get_ha()
    va = label_artist.get_va()

    # Capture the artist's anchor in figure coordinates before we wipe it.
    # The label uses its own transform (typically blended axes/figure
    # coords); converting through display space gives us a stable point we
    # can re-render at via ``fig.transFigure``.
    transform = label_artist.get_transform()
    x_disp, y_disp = transform.transform(label_artist.get_position())
    x_fig, y_fig = fig.transFigure.inverted().transform((x_disp, y_disp))

    # Hide the original — leave the artist in place so matplotlib's layout
    # bookkeeping (label padding, ``get_window_extent`` for the source-line
    # placement code) doesn't get confused by a missing label.
    label_artist.set_text("")

    render_text_with_superscripts(
        fig,
        x_fig,
        y_fig,
        text,
        fontsize=fontsize,
        fontproperties=fp,
        color=color,
        va=va,
        ha=ha,
    )


def _figure_legends(fig) -> list:
    """Every legend on ``fig`` — figure legends plus each axes' own legend.

    Covers the library's own :func:`~graphs.top_legend` (a figure legend) and
    :func:`~graphs.smart_legend` (a corner axes legend or its top-legend
    fallback) as well as plain ``ax.legend()`` / ``fig.legend()`` calls.
    """
    legends = list(fig.legends)
    for axes in fig.axes:
        legend = axes.get_legend()
        if legend is not None:
            legends.append(legend)
    return legends


def _superscript_legend_texts(fig) -> None:
    """Re-render legend entry texts so footnote markers become superscripts.

    A legend label like ``"Self-attributed*"`` renders its marker inline at
    full size — matplotlib legend entries are single ``Text`` artists. For each
    entry containing a marker, this captures the artist's anchor in figure
    coordinates, makes the original invisible (``alpha=0`` — the text is kept
    so the legend's own layout, the footnote anchor scan and ``verify_layout``
    still see it and the legend box doesn't reflow), and re-renders the string
    at the same anchor through :func:`render_text_with_superscripts`. The
    overlay artists take a zorder above the legend's so a framed legend can't
    paint over them. Runs at the end of ``finalize`` (after any ``top_legend``
    re-anchor, so the measured positions are final); processed entries are
    tagged and skipped on a repeated ``finalize``.

    Limitations:
      * The overlay is anchored in figure coordinates. Legends the library
        manages (``smart_legend`` corner legends, an auto ``top_legend``
        re-anchored by ``finalize``) track those coordinates exactly through
        ``savefig(bbox_inches="tight")``; a raw ``fig.legend()`` or an
        explicit-``y`` ``top_legend`` is re-anchored against the cropped
        figure box at save time and can shift a few pixels relative to the
        overlay.
    """
    entries = [t for leg in _figure_legends(fig) for t in leg.get_texts()]
    if not any(_has_marker(t.get_text()) for t in entries):
        return

    fig.canvas.draw()
    inv = fig.transFigure.inverted()
    for entry in entries:
        text = entry.get_text()
        if not text or not _has_marker(text):
            continue
        if getattr(entry, "_graphs_superscripted", False):
            continue
        x_disp, y_disp = entry.get_transform().transform(entry.get_position())
        x_fig, y_fig = inv.transform((x_disp, y_disp))
        n_texts_before = len(fig.texts)
        render_text_with_superscripts(
            fig,
            x_fig,
            y_fig,
            text,
            fontsize=entry.get_fontsize(),
            fontproperties=entry.get_fontproperties(),
            color=entry.get_color(),
            va=entry.get_va(),
            ha=entry.get_ha(),
        )
        # Framed figure legends draw at zorder 5 — above default fig.text
        # (zorder 3) — so lift the overlay chunks clear of the frame.
        for chunk in fig.texts[n_texts_before:]:
            chunk.set_zorder(entry.get_zorder() + 3)
        entry.set_alpha(0.0)
        entry._graphs_superscripted = True


def dark_zero_line(ax, *, skip_axhline: bool = False) -> None:
    """Draw a strong dark rule on the zero baseline a chart's data straddles.

    No-op unless the y-range strictly spans 0 *and* the axes has visible y
    gridlines — a numeric value axis. Categorical axes (``bar_h`` rows,
    thermometer categories) have their y grid off, so they never pick up a
    spurious centreline even though their tick positions span 0.

    Recolours the zero gridline (so its ``y_labels_on_grid`` gutter extension
    inherits the dark stroke and "0" sits on a full-width rule) and keeps the
    gridline's own ``axisbelow`` zorder, so the rule stays *under* every data
    line. Falls back to an ``axhline`` when there are gridlines but none lands
    on zero.

    ``finalize`` calls this automatically (see its ``zero_rule`` argument).
    Call it directly per panel on a faceted figure, where ``finalize`` only
    finishes the primary axes.

    Args:
        ax: Axes whose zero baseline should carry the rule.
        skip_axhline: When the caller already drew their own zero rule (a
            manual ``axhline(0)``, e.g. one that sits *over* the data), pass
            ``True``. The zero gridline is still recoloured — so its gutter
            extension matches the manual rule rather than reading as a broken
            grey stub — but no duplicate ``axhline`` is added.
    """
    y_lo, y_hi = sorted(ax.get_ylim())
    if not y_lo < 0.0 < y_hi:
        return
    # A tiny dip below zero from cosmetic ylim padding (e.g. ``set_ylim(-0.01, ...)``
    # on an all-non-negative chart, for breathing room under the baseline) is not a
    # genuine straddle. Ruling zero there recolours the 0-gridline dark on top of the
    # black bottom spine — a doubled baseline. Only rule zero when a real negative
    # y-tick is present (genuine +/- data), not merely a padded y-limit.
    if not any(loc < -1e-9 * (y_hi - y_lo) for loc in ax.get_yticks() if y_lo <= loc <= y_hi):
        return
    gridlines = ax.get_ygridlines()
    if not any(g.get_visible() for g in gridlines):
        return  # categorical / grid-off y-axis: no zero centreline
    span = max(1.0, y_hi - y_lo)
    zero_grid = next(
        (
            g
            for loc, g in zip(ax.get_yticks(), gridlines)
            if abs(loc) <= 1e-9 * span and g.get_visible()
        ),
        None,
    )
    if zero_grid is not None:
        # Keep the gridline's own (axisbelow) zorder so the rule stays under
        # every data line, exactly like the lighter gridlines.
        zero_grid.set(color=C_SPINE, linewidth=1.0)
    elif not skip_axhline:
        ax.axhline(0.0, color=C_SPINE, linewidth=1.0, zorder=0.5)


def _check_ylabel(ax, *, allow_ylabel: bool) -> None:
    """Raise when the axes carries a hardcoded y-axis label.

    The title/descriptor *is* the y-axis label (graph-design "Headline
    conventions"): name the measured quantity and its units in
    ``finalize(descriptor=...)`` and leave ``ax.set_ylabel("")``. A hardcoded
    axis label duplicates — or silently contradicts — the descriptor and breaks
    the title-stack convention. For a horizontal Economist-style axis title use
    :func:`y_axis_label`, which renders through ``fig.text`` rather than
    ``set_ylabel`` and so never trips this check.

    The genuine exceptions the runtime can't tell apart from a mistake — a
    ``twinx()`` secondary axis, or a coordinate plot (ROC with y=TPR / x=FPR, a
    scatter whose two axes are both dimensions) where an axis legitimately needs
    its own label — pass ``allow_ylabel=True``. This mirrors the static
    ``enforcement/rules/no-hardcoded-ylabel.yml`` ast-grep rule (whose escape
    hatch is a trailing ``# ast-grep-ignore: no-hardcoded-ylabel``), so a chart
    is held to the same rule whether it is linted or merely run.
    """
    if allow_ylabel:
        return
    label = ax.get_ylabel().strip()
    if not label:
        return
    raise ValueError(
        f"graphs.finalize: the axes has a hardcoded y-axis label {label!r}. The "
        "title/descriptor IS the y-axis label — name the measured quantity + "
        'units in finalize(descriptor=...) and leave ax.set_ylabel(""). For a '
        "horizontal Economist-style axis title use graphs.y_axis_label(ax, ...). "
        "For a genuine coordinate plot (ROC / scatter, both axes dimensions) or "
        "a twinx() secondary axis, pass finalize(..., allow_ylabel=True)."
    )


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
    marker: str = "delta",
    footnote_lines: int = 0,
    y_labels: str = "on_grid",
    panel_labels: bool = False,
    auto_layout: bool = True,
    zero_rule: bool = True,
    allow_ylabel: bool = False,
):
    """Add Economist finishing touches to an axes object.

    Title stack (top to bottom)::

        Δ           red delta glyph (or short red rule when marker="rule")
        Title       IBM Plex Sans Bold
        Descriptor  IBM Plex Sans Regular

    Auto-layout always runs and sizes **all four margins plus inter-panel
    spacing** with the renderer, so callers don't hand-set ``subplots_adjust``:

    * **Top / bottom** fit the title-stack and the source/footnote band over
      the measured x-tick label height.
    * **Left / right** are measured from the actual y-axis text — the side a
      chart's y-tick labels (and ``y_axis_label`` / direct ``label_lines``)
      land on gets a margin wide enough to hold them, the other side keeps the
      small default. So a right-axis line chart keeps a tight left and a
      measured right; a horizontal bar chart with long category labels on the
      left gets a measured wide left.
    * **Inter-panel ``wspace`` / ``hspace``** are sized for a grid of axes
      (``len(fig.axes) > 1``): ``wspace`` from the inter-column y-label width
      (independent-y panels get more than shared-y), ``hspace`` from the
      x-tick band plus, when ``panel_labels=True``, the ``panel_label``
      heading height between rows.

    Any ``subplots_adjust`` the caller set *before* ``finalize`` is therefore
    overwritten. A caller may still re-apply ``subplots_adjust`` *after*
    ``finalize`` to override a specific value (the figures that anchor bespoke
    artists into a hand-sized gutter, e.g. ``wework``'s band labels, do this).

    On a non-Agg backend (no measurable renderer) the side margins and
    inter-panel spacing fall back to today's fixed constants.

    The ``auto_layout`` keyword is accepted but **ignored** (deprecated): it
    used to gate this behaviour and is kept only so existing callers passing
    ``auto_layout=False`` keep working — auto-layout now always runs.

    Args:
        title: Chart headline. Auto-wrapped to the figure width — pass it
            as one line; explicit ``\\n`` still forces a break.
        descriptor: Subtitle line (country, metric, unit). Auto-wrapped like
            the title; use ``\\n`` only for semantic breaks (subject / unit).
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
        marker: Top-of-stack anchor. ``"delta"`` (default) renders a red Δ
            glyph; ``"rule"`` draws the legacy short red horizontal line;
            ``"none"`` skips the marker entirely.
        footnote_lines: Extra lines of ``footnotes()`` text below the chart.
            Auto-layout reserves an additional ~7pt-line per footnote row so
            wrapped notes don't clip. Only needed on multi-row grids (whose
            bottom margin can't grow after ``panel_label``) — on single-row
            figures ``footnotes()`` measures its own wrapped rows and grows
            the bottom margin itself.
        y_labels: ``"on_grid"`` (default) sits numeric y tick labels on
            gridlines that extend under them (``y_labels_on_grid``); applied
            only when the axes has visible y gridlines, so categorical
            charts are unaffected. ``"ticks"`` keeps native tick labels.
        panel_labels: Set ``True`` when a faceted layout adds a ``panel_label``
            heading to each panel *after* ``finalize``. The top margin then
            reserves the rule-and-label band above the top row (so the heading
            can't collide with the axes below or an auto ``top_legend`` above —
            the stack becomes legend → panel label → axes), and on a multi-row
            grid the auto ``hspace`` reserves the same height between rows.
        zero_rule: When the y-range straddles 0, draw a strong dark rule on
            the zero baseline (a centreline the data crosses) unless the
            caller already drew their own. Default ``True``. Set ``False`` for
            horizontal-value charts whose y-axis is a coordinate that merely
            spans 0 (e.g. a latitude axis through the equator), where the
            value baseline is the vertical x=0 line instead.
        allow_ylabel: Opt out of the hardcoded-y-label guard. ``finalize``
            raises when the axes carries a non-empty ``ax.set_ylabel(...)`` —
            the descriptor is meant to carry the y-axis quantity (see the class
            docstring and ``y_axis_label``). Pass ``True`` for the genuine
            exceptions the runtime can't tell from a mistake: a coordinate plot
            (ROC / scatter, both axes dimensions) or a ``twinx()`` secondary
            axis.

    Raises:
        ValueError: If the axes has a hardcoded non-empty y-axis label and
            ``allow_ylabel`` is not set — the descriptor should name the
            measured quantity, or use :func:`y_axis_label` for a horizontal
            axis title.
    """
    if marker not in ("delta", "rule", "none"):
        raise ValueError(f"marker must be 'delta', 'rule', or 'none', got {marker!r}")
    if y_labels not in ("on_grid", "ticks"):
        raise ValueError(f"y_labels must be 'on_grid' or 'ticks', got {y_labels!r}")
    _check_ylabel(ax, allow_ylabel=allow_ylabel)
    fig = ax.get_figure()

    # Wrap the title stack to the figure's own width BEFORE pad computation
    # (which counts lines). Explicit "\n" survives — only overflowing lines
    # gain breaks — so the wrap is owned by this figure's geometry, never
    # copied from a reference layout.
    wrap_x0 = title_x if title_x is not None else AUTO_LAYOUT_LEFT
    if title:
        title_indent = 0.0
        if marker == "delta":
            marker_w_fig = (
                (TITLE_SIZE_PT * MARKER_SIZE_RATIO) / 72.0 / fig.get_figwidth()
            )
            marker_gap_fig = MARKER_GAP_PT / 72.0 / fig.get_figwidth()
            title_indent = marker_w_fig + marker_gap_fig
        fp_title_wrap = fm.FontProperties(
            family=_get_font(), weight=TITLE_WEIGHT, size=TITLE_SIZE_PT
        )
        title = _wrap_to_fig_width(
            fig,
            title,
            fontproperties=fp_title_wrap,
            avail_fig_w=AUTO_LAYOUT_RIGHT - wrap_x0 - title_indent,
        )
    # The semibold descriptor lead is keyed to the EXPLICIT "\n" (the
    # semantic subject / unit split), never to breaks added by the wrap —
    # so capture the boundary before wrapping. The lead wraps measured at
    # its rendered (semibold) width.
    desc_lead = ""
    if descriptor:
        fp_desc_wrap = fm.FontProperties(
            family=_get_font_condensed(), weight="normal", size=DESCRIPTOR_SIZE_PT
        )
        desc_avail_w = AUTO_LAYOUT_RIGHT - wrap_x0
        if "\n" in descriptor:
            lead_raw, rest_raw = descriptor.split("\n", 1)
            fp_desc_lead_wrap = fm.FontProperties(
                family=_get_font_condensed(),
                weight="semibold",
                size=DESCRIPTOR_SIZE_PT,
            )
            desc_lead = _wrap_to_fig_width(
                fig,
                lead_raw,
                fontproperties=fp_desc_lead_wrap,
                avail_fig_w=desc_avail_w,
            )
            desc_rest = _wrap_to_fig_width(
                fig,
                rest_raw,
                fontproperties=fp_desc_wrap,
                avail_fig_w=desc_avail_w,
            )
            descriptor = f"{desc_lead}\n{desc_rest}"
        else:
            descriptor = _wrap_to_fig_width(
                fig,
                descriptor,
                fontproperties=fp_desc_wrap,
                avail_fig_w=desc_avail_w,
            )

    _check_x_monotonic(ax)
    if autoscale_y:
        _autoscale_y(ax)

    # Move the y-axis to the right (and set the final tick pad) BEFORE measuring
    # side margins — the protrusion measurement reads the labels on whichever
    # side they end up on, so the flip must happen first.
    if y_axis_right:
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    # Preserve any larger pad set by chart helpers (e.g. bar_h sizes pad
    # to clear the widest left-edge label). Only fall back to the 4pt
    # default when the existing pad is smaller.
    current_pad = (
        ax.yaxis.get_major_ticks()[0].get_pad() if ax.yaxis.get_major_ticks() else 0
    )
    ax.yaxis.set_tick_params(
        pad=max(current_pad, TICK_PAD_MIN), labelsize=TICK_LABEL_SIZE_PT
    )
    ax.spines["bottom"].set_color(C_SPINE)
    ax.spines["bottom"].set_linewidth(1.0)

    # An auto-positioned ``top_legend`` (tagged by ``top_legend`` when called
    # with no explicit ``y=``) sits in a band between the title-stack and the
    # axes. Measure its height now so the top margin reserves room for it; the
    # legend is re-anchored to the final axes top further below.
    top_legend = _top_legend(fig)
    fig_h_in = fig.get_figheight()
    legend_gap = AUTO_LAYOUT_TOP_LEGEND_GAP_PT / 72.0 / fig_h_in
    top_legend_band = 0.0
    if top_legend is not None:
        legend_h = _top_legend_height_fig(fig, top_legend)
        if legend_h:
            top_legend_band = legend_h + legend_gap

    # A top-row ``panel_label`` (rule + bold heading, drawn *above* the axes top
    # after ``finalize``) needs its own band in the top margin, or it lands on
    # the axes / an overlying top legend. ``panel_labels=True`` is the caller's
    # signal that they'll add these headings; reserve the same rule-and-label
    # height the inter-row ``hspace`` uses. Single-row and multi-row grids alike
    # gain it — every row's panel label draws above its own axes top, and the
    # top row's is the one that eats the top margin.
    top_panel_label_band = (
        AUTO_LAYOUT_PANEL_LABEL_PT / 72.0 / fig_h_in if panel_labels else 0.0
    )

    # A pre-``finalize`` ``y_axis_label`` (tagged on the figure at render time)
    # occupies a strip just above the axes top. Measure the tallest block and
    # reserve a band for it so the descriptor — and the whole title stack —
    # seats above the label instead of overlapping it; the label artists are
    # re-anchored to the final axes top after auto-layout below.
    y_label_specs = _y_axis_label_specs(fig)
    y_axis_label_band = 0.0
    if y_label_specs:
        label_block = _y_axis_label_band_fig(fig, y_label_specs)
        if label_block:
            y_axis_label_band = (
                label_block + AUTO_LAYOUT_Y_AXIS_LABEL_GAP_PT / 72.0 / fig_h_in
            )

    # Auto-layout always runs — size every margin and the inter-panel spacing
    # from the renderer. Top/bottom fit the title-stack and source band;
    # left/right are measured from the actual y-axis text; wspace/hspace size a
    # grid of panels. Callers may still override a specific value afterwards.
    top_pad, bottom_pad = _compute_auto_pads(
        fig,
        ax,
        title=title,
        descriptor=descriptor,
        source=source,
        marker=marker,
        y_start=y_start,
        footnote_lines=footnote_lines,
        top_legend_band=top_legend_band,
        top_panel_label_band=top_panel_label_band,
        y_axis_label_band=y_axis_label_band,
    )
    left, right = _compute_side_margins(fig)
    adjust_kwargs = {
        "top": 1.0 - top_pad,
        "bottom": bottom_pad,
        "left": left,
        "right": right,
    }
    wspace = _compute_wspace(fig)
    if wspace is not None:
        adjust_kwargs["wspace"] = wspace
    hspace = _compute_hspace(fig, has_panel_labels=panel_labels)
    if hspace is not None:
        adjust_kwargs["hspace"] = hspace
    fig.subplots_adjust(**adjust_kwargs)
    fig.canvas.draw()

    # One bounded corrective pass: a centred outer x-tick label can hang half
    # its width past the figure edge (not shift-invariant, so it couldn't be
    # folded into the y-based margins above). Nudge the affected side in once.
    spill = _xtick_side_spill(fig)
    if spill is not None and (spill[0] > 0 or spill[1] > 0):
        new_left = adjust_kwargs["left"] + spill[0]
        new_right = adjust_kwargs["right"] - spill[1]
        if new_left < new_right:  # never invert the axes
            fig.subplots_adjust(left=new_left, right=new_right)
            fig.canvas.draw()

    # Auto-layout moved the axes; shift every pre-``finalize`` ``y_axis_label``
    # block back onto its axes' final top edge (the reserved band above it
    # keeps the title stack clear).
    if y_label_specs:
        _reanchor_y_axis_labels(fig)

    bbox = ax.get_position()
    tx = title_x if title_x is not None else bbox.x0

    # Build title stack upward from just above the axes.
    # Gaps tuned against The Economist's web-styleguide reference: rule sits
    # ~6pt above the title cap-height, title sits ~3pt above the descriptor's
    # top ascender, descriptor lines lead at ~1.2x. All vertical advances are
    # computed from points so spacing stays visually consistent across the
    # full range of figure heights (3.6"–5.5") in the examples library.
    fig_h_in = fig.get_figheight()
    pt2fig = 1.0 / 72.0 / fig_h_in  # 1 typographic point in figure-y coords
    line_gap = INTER_BLOCK_GAP_PT * pt2fig
    rule_gap = RULE_GAP_PT * pt2fig
    y_cursor = bbox.y1 + y_start

    # If x-tick labels render above the axes top (e.g. bar_h puts them on top,
    # or a secondary_xaxis("top") mirrors the bottom ticks), push the title
    # stack above the highest tick label so they don't overlap.
    try:
        renderer = fig.canvas.get_renderer()
        highest_fig_y = bbox.y1
        # Collect tick labels from the main axes + any secondary x-axes
        # created via ``ax.secondary_xaxis("top")``. Those live on
        # ``ax.child_axes`` rather than ``fig.axes``.
        tick_labels = list(ax.get_xticklabels())
        for child in getattr(ax, "child_axes", []):
            tick_labels.extend(child.get_xticklabels())
        for tl in tick_labels:
            if not tl.get_text() or not tl.get_visible():
                continue
            tl_bb = tl.get_window_extent(renderer=renderer)
            top_y = tl_bb.transformed(fig.transFigure.inverted()).y1
            if top_y > highest_fig_y:
                highest_fig_y = top_y
        if highest_fig_y > bbox.y1:
            y_cursor = highest_fig_y + TOP_TICK_CLEARANCE_PT * pt2fig
    except Exception:
        pass

    # A re-anchored ``y_axis_label`` block sits immediately above the axes top.
    # Advance the title-stack cursor past its reserved band so the descriptor —
    # and an auto top legend — seat above the label instead of on top of it.
    if y_axis_label_band > 0.0:
        y_cursor = max(y_cursor, bbox.y1 + y_axis_label_band)

    # A top-row ``panel_label`` occupies the band immediately above the axes top
    # (rule + bold heading, drawn after ``finalize``). Advance the title-stack
    # cursor past its reserved band so everything above — an auto top legend, the
    # descriptor, the title — seats above the heading instead of on top of it.
    if top_panel_label_band > 0.0:
        y_cursor = max(y_cursor, bbox.y1 + top_panel_label_band)

    # Place an auto top_legend in the reserved band: its bottom sits at the
    # current title-stack base (just above the axes / top-mounted ticks), so it
    # spans above the row of panels on a faceted chart. ``finalize`` reserved
    # ``top_legend_band`` (legend height + gap) above the axes for it; advance
    # the title-stack cursor past the band so the descriptor lands above the
    # legend, never on it. The legend's ``loc="upper *"`` puts the anchor at its
    # TOP, so anchor at ``y_cursor + legend_h`` to seat the bottom at y_cursor.
    #
    # The anchor's y is bound in AXES-fraction (x stays figure-fraction) via a
    # blended transform: ``savefig(bbox_inches="tight")`` shifts a pure
    # ``transFigure`` legend independently of the ``fig.text`` title-stack
    # (re-anchoring it against the cropped figure box), which re-opens the very
    # collision this reserves against. An axes-relative y crops in lockstep with
    # the axes and the descriptor, so the gap survives the tight save.
    if top_legend is not None and top_legend_band > 0.0:
        spec = top_legend._graphs_top_legend
        legend_h = top_legend_band - legend_gap
        anchor_fig_y = y_cursor + legend_h
        anchor_axes_y = (anchor_fig_y - bbox.y0) / bbox.height
        blended = mtransforms.blended_transform_factory(fig.transFigure, ax.transAxes)
        top_legend.set_bbox_to_anchor((spec.x, anchor_axes_y), transform=blended)
        y_cursor += top_legend_band

    if descriptor:
        desc_lines = descriptor.split("\n")
        n_desc_lines = len(desc_lines)
        fp_desc = fm.FontProperties(family=_get_font_condensed(), weight="normal")
        if desc_lead:
            # An explicit "\n" splits the descriptor into a semibold lead
            # (the subject — every line it wrapped to) over regular
            # continuation lines (scope/units). Auto-wrap breaks alone
            # never trigger the lead styling.
            n_lead_lines = desc_lead.count("\n") + 1
            n_rest_lines = n_desc_lines - n_lead_lines
            fp_desc_lead = fm.FontProperties(
                family=_get_font_condensed(), weight="semibold"
            )
            render_text_with_superscripts(
                fig,
                tx,
                y_cursor,
                "\n".join(desc_lines[n_lead_lines:]),
                fontsize=DESCRIPTOR_SIZE_PT,
                fontproperties=fp_desc,
                color=C_SPINE,
                va="bottom",
                ha="left",
                linespacing=DESCRIPTOR_LINESPACING,
            )
            render_text_with_superscripts(
                fig,
                tx,
                y_cursor + DESCRIPTOR_LINE_BOX_PT * pt2fig * n_rest_lines,
                desc_lead,
                fontsize=DESCRIPTOR_SIZE_PT,
                fontproperties=fp_desc_lead,
                color=C_SPINE,
                va="bottom",
                ha="left",
                linespacing=DESCRIPTOR_LINESPACING,
            )
        else:
            render_text_with_superscripts(
                fig,
                tx,
                y_cursor,
                descriptor,
                fontsize=DESCRIPTOR_SIZE_PT,
                fontproperties=fp_desc,
                color=C_SPINE,
                va="bottom",
                ha="left",
                linespacing=DESCRIPTOR_LINESPACING,
            )
        # Descriptor line box ≈ 9.5pt × 1.20 ≈ 11.4pt for each line.
        y_cursor += DESCRIPTOR_LINE_BOX_PT * pt2fig * n_desc_lines + line_gap

    if title:
        n_title_lines = title.count("\n") + 1
        fp = fm.FontProperties(family=_get_font(), weight=TITLE_WEIGHT)
        title_size_pt = TITLE_SIZE_PT

        if marker == "delta":
            # Inline layout: triangle's height matches the title's cap-height
            # (apex at cap-top, bottom edge at baseline). IBM Plex Sans Bold
            # cap-height ≈ 0.72 × em size. A small upward nudge compensates
            # for matplotlib's baseline placement so the bottom of the
            # triangle visually lines up with the bottom of "B".
            marker_size_pt = title_size_pt * MARKER_SIZE_RATIO
            marker_w_fig = marker_size_pt / 72.0 / fig.get_figwidth()
            marker_gap_fig = (MARKER_GAP_PT * pt2fig) * (
                fig.get_figheight() / fig.get_figwidth()
            )
            title_x_inline = tx + marker_w_fig + marker_gap_fig
            # Multi-line text with va="baseline" anchors the LAST line's
            # baseline at y_cursor; the triangle belongs on the FIRST line.
            first_baseline = y_cursor + (
                (n_title_lines - 1) * title_size_pt * TITLE_LINESPACING * pt2fig
            )
            _draw_logo_triangle(fig, tx, first_baseline, size_pt=marker_size_pt)
            render_text_with_superscripts(
                fig,
                title_x_inline,
                y_cursor,
                title,
                fontsize=title_size_pt,
                fontproperties=fp,
                color=C_SPINE,
                va="baseline",
                ha="left",
                linespacing=TITLE_LINESPACING,
            )
            y_cursor += TITLE_LINE_BOX_PT * pt2fig * n_title_lines
        else:
            # Standard above-title layout: title at y_cursor, rule (if any)
            # rendered above with a small gap.
            render_text_with_superscripts(
                fig,
                tx,
                y_cursor,
                title,
                fontsize=title_size_pt,
                fontproperties=fp,
                color=C_SPINE,
                va="bottom",
                ha="left",
                linespacing=TITLE_LINESPACING,
            )
            y_cursor += TITLE_LINE_BOX_PT * pt2fig * n_title_lines + rule_gap
            if marker == "rule":
                _draw_rule(fig, tx, y_cursor)
    elif marker == "delta":
        _draw_delta(fig, tx, y_cursor)
    elif marker == "rule":
        _draw_rule(fig, tx, y_cursor)

    if source:
        # Place source below the lowest of: xlabel, x-tick labels.
        # Wrapped multi-line x-tick labels can extend further down than the
        # xlabel and previously caused the source line to overlap them.
        source_y = bbox.y0 - SOURCE_Y_OFFSET
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
            source_y = min(source_y, lowest_fig_y - SOURCE_TICK_CLEARANCE)
        except Exception:
            pass
        fp_src = fm.FontProperties(family=_get_font_condensed(), weight="light")
        source_clean, source_urls = strip_links(source)
        render_text_with_superscripts(
            fig,
            tx,
            source_y,
            source_clean,
            fontsize=SOURCE_SIZE_PT,
            fontproperties=fp_src,
            color=C_SOURCE,
            va="top",
            ha="left",
            url_spans=source_urls,
        )

    # Post-process axis labels so footnote markers in ``set_xlabel`` /
    # ``set_ylabel`` strings render as superscripts. Runs after the source
    # line is placed so the xlabel's window-extent is still available for
    # the clearance calculation above.
    _superscript_axis_label(ax, "x")
    _superscript_axis_label(ax, "y")

    # House default: a strong dark rule on a zero baseline the data straddles
    # (a centreline). Skipped when the caller already drew their own zero rule,
    # so manual ``axhline(0)`` charts don't double up.
    has_zero_rule = any(
        len(ln.get_ydata()) and all(abs(v) < 1e-12 for v in ln.get_ydata())
        for ln in ax.lines
    )
    if zero_rule:
        # Still recolour the zero gridline when a manual rule exists, so its
        # on-grid gutter extension matches; only skip adding a duplicate line.
        dark_zero_line(ax, skip_axhline=has_zero_rule)

    # House default: numeric y labels sit on gridlines that extend under
    # them. Gated on visible y gridlines so categorical axes (bar_h rows,
    # thermometer categories) keep their native labels.
    if y_labels == "on_grid" and any(g.get_visible() for g in ax.get_ygridlines()):
        from graphs._labels import y_labels_on_grid

        y_labels_on_grid(ax)

    # Post-process legend entry texts so footnote markers ("Self-attributed*")
    # render as superscripts, exactly as they do in the title, descriptor,
    # source and axis labels. Runs last: the top_legend re-anchor above must
    # settle before the entries' positions are measured.
    _superscript_legend_texts(fig)

    return fig, ax


def panel_label(ax, label: str, *, fontsize: int = PANEL_LABEL_SIZE_PT) -> None:
    """Bold panel sub-heading with a short dark rule — for faceted charts.

    Renders above the axes::

        --------
        Economic
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    bbox = ax.get_position()

    rule_w = PANEL_RULE_WIDTH_PX / (fig.get_figwidth() * fig.dpi)
    fig.add_artist(
        plt.Line2D(
            [bbox.x0, bbox.x0 + rule_w],
            [bbox.y1 + PANEL_RULE_Y_OFFSET, bbox.y1 + PANEL_RULE_Y_OFFSET],
            transform=fig.transFigure,
            color=C_SPINE,
            linewidth=PANEL_RULE_LINEWIDTH,
            solid_capstyle="butt",
            clip_on=False,
        )
    )
    fig.text(
        bbox.x0,
        bbox.y1 + PANEL_LABEL_Y_OFFSET,
        label,
        transform=fig.transFigure,
        fontsize=fontsize,
        fontweight="bold",
        color=C_TEXT,
        va="bottom",
        ha="left",
    )


def x_axis_label(
    ax,
    text: str,
    *,
    color: str | None = None,
    fontsize: float = Y_AXIS_LABEL_SIZE_PT,
    labelpad: float | None = None,
) -> None:
    """Set the x-axis label with project-default colour and size.

    Thin wrapper around ``ax.set_xlabel`` that applies ``C_SPINE`` colour
    and the standard axis-label point size. Footnote markers (``*``, ``†``,
    ``‡``, ``§``) in ``text`` are auto-superscripted by ``finalize`` via its
    post-processing pass — no separate call needed.
    """
    color = color if color is not None else C_SPINE
    kwargs: dict = {"color": color, "fontsize": fontsize}
    if labelpad is not None:
        kwargs["labelpad"] = labelpad
    ax.set_xlabel(text, **kwargs)


def y_axis_label(
    ax,
    text: str,
    *,
    unit: str | None = None,
    side: str = "right",
    width_frac: float = 0.5,
    fontsize: float = Y_AXIS_LABEL_SIZE_PT,
    color: str | None = None,
    unit_color: str | None = None,
) -> None:
    """Economist-style horizontal y-axis title above the axis.

    Renders ``text`` word-wrapped to ~``width_frac`` of the axes width, aligned
    flush with the appropriate side of the chart, sitting just above
    ``bbox.y1``. Use instead of ``ax.set_ylabel`` for the Economist look.

    When ``unit`` is provided, it is rendered on a second line below ``text``
    in a lighter colour (``C_LABEL_MUTED`` by default) — the Economist
    convention for "metric / unit" stacked labels.

    **Call it before ``finalize``** (like ``top_legend``): the rendered block
    is tagged on the figure, and ``finalize`` reserves a band for it between
    the descriptor and the axes top, then re-anchors it to the final axes
    position — so a tall title stack can never overlap the label. Calling it
    *after* ``finalize`` is manual placement: the label lands just above the
    final axes top with no reserved room, which collides with the descriptor
    whenever the stack reaches the label's side of the chart.

    Args:
        text: Label text (will be word-wrapped).
        unit: Optional unit string rendered on a second line in ``unit_color``.
        side: ``"right"`` (default — matches the y-axis-right convention) or
            ``"left"``.
        width_frac: Wrap width as a fraction of the axes pixel width.
        fontsize: Font size in points.
        color: Primary text colour; defaults to the spine colour.
        unit_color: Colour for the ``unit`` line; defaults to ``C_LABEL_MUTED``.
    """
    if side not in ("right", "left"):
        raise ValueError(f"side must be 'right' or 'left', got {side!r}")

    fig = ax.get_figure()
    fig.canvas.draw()
    bbox = ax.get_position()

    # Estimate wrap width in characters: axes width in px * width_frac, divided
    # by ~0.55em-per-char for IBM Plex Sans Condensed at the chosen size.
    ax_px_w = bbox.width * fig.get_figwidth() * fig.dpi
    char_px = max(fontsize * 0.55, 1.0)
    n_chars = max(int(ax_px_w * width_frac / char_px), 8)

    wrapped = textwrap.fill(text, width=n_chars, max_lines=2, placeholder="…")

    x = bbox.x1 if side == "right" else bbox.x0
    ha = "right" if side == "right" else "left"
    fp = fm.FontProperties(family=_get_font_condensed(), weight="medium")
    n_texts_before = len(fig.texts)

    fig_h_in = fig.get_figheight()
    pt2fig = 1.0 / 72.0 / fig_h_in
    # Line box ≈ fontsize * 1.2 points; advance the cursor by one line per
    # wrapped text line so the unit sits just below the main label.
    line_h = fontsize * Y_AXIS_LABEL_LINESPACING * pt2fig
    n_text_lines = wrapped.count("\n") + 1
    y_text = bbox.y1 + Y_AXIS_LABEL_MARGIN
    if unit:
        y_text += line_h  # leave room below for the unit line

    render_text_with_superscripts(
        fig,
        x,
        y_text,
        wrapped,
        fontsize=fontsize,
        fontproperties=fp,
        color=color if color is not None else C_SPINE,
        va="bottom",
        ha=ha,
        linespacing=Y_AXIS_LABEL_LINESPACING,
    )

    if unit:
        # Anchor the unit line directly under the wrapped text block.
        y_unit = y_text - line_h * n_text_lines
        render_text_with_superscripts(
            fig,
            x,
            y_unit,
            unit,
            fontsize=fontsize,
            fontproperties=fp,
            color=unit_color if unit_color is not None else C_LABEL_MUTED,
            va="bottom",
            ha=ha,
            linespacing=Y_AXIS_LABEL_LINESPACING,
        )

    # Tag the rendered block on the figure so a later ``finalize`` can reserve
    # a band for it in the top margin and re-anchor it to the final axes top
    # (see ``_YAxisLabelSpec``). The artist list is the delta of ``fig.texts``
    # across the render, so superscript chunk splits are captured too.
    specs = getattr(fig, "_graphs_y_axis_labels", None)
    if specs is None:
        specs = []
        fig._graphs_y_axis_labels = specs
    specs.append(
        _YAxisLabelSpec(
            ax=ax,
            artists=list(fig.texts[n_texts_before:]),
            axes_top=bbox.y1,
            anchor_x=x,
            side=side,
        )
    )


def save_chart(
    script_file, *, dpi: int = 150, close: bool = True, verbose: bool = True
):
    """Save the current figure next to ``script_file`` as ``<stem>.png``.

    The standard example-script epilogue (``bbox_inches="tight"``, 150 dpi,
    close, confirmation print) as one call::

        save_chart(__file__)

    Args:
        script_file: Almost always ``__file__`` — the output lands beside
            the script, named after it.
        dpi: Raster resolution.
        close: Close the current figure after saving.
        verbose: Print a one-line confirmation.

    Returns:
        Path of the written PNG.
    """
    from pathlib import Path

    out = Path(script_file).resolve().with_suffix(".png")
    plt.savefig(out, bbox_inches="tight", dpi=dpi)
    if close:
        plt.close()
    if verbose:
        print(f"Saved {out.name}")
    return out


def year_ticks(ax, years, *, inset: bool = True) -> None:
    """Numeric-axis year ticks with Economist abbreviation.

    For integer year axes (bar charts and the like, where ``year_axis``'s
    date machinery doesn't apply): the first tick and century ticks render
    in full (``1950``, ``2000``), the rest as two digits (``60``, ``10``).

        year_ticks(ax, [1950, 1960, ..., 2000, 2010, 2019])

    Args:
        ax: Axes with a numeric x-axis in calendar years.
        years: Tick positions (ints). The first is always rendered in full.
        inset: Also apply ``inset_tick_labels`` so the end labels stay
            inside the plot bounds (the usual convention; pass False when
            the axis has generous margins).
    """
    years = list(years)
    labels = [
        str(y) if i == 0 or y % 100 == 0 else f"{y % 100:02d}"
        for i, y in enumerate(years)
    ]
    ax.set_xticks(years)
    ax.set_xticklabels(labels)
    if inset:
        from graphs._labels import inset_tick_labels

        inset_tick_labels(ax, axis="x")


def x_axis_top(
    ax, *, labelsize: float = TICK_LABEL_SIZE_PT, length: float = 3.5
) -> None:
    """Move the x-axis to the top of the plot (horizontal-chart convention).

    Economist horizontal bars, lollipops and latitude profiles read the
    value axis along the top. Applies the standard tick styling and hides
    the bottom spine.

    Call AFTER ``finalize()`` when a legend row sits between the title and
    the axis — finalize pins the title stack directly above top-mounted
    tick labels, which would leave no room for the legend otherwise.
    """
    ax.xaxis.tick_top()
    ax.xaxis.set_tick_params(labelsize=labelsize, length=length, direction="out")
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


def year_axis(ax, *, abbreviate: bool = True, set_locator: bool = True) -> None:
    """Format a date x-axis with full-year-then-abbreviated-year ticks.

    Economist convention: the leftmost visible year tick renders as a
    full year (e.g. ``2016``) and every subsequent tick is abbreviated
    (e.g. ``'17``, ``'18``). When ``abbreviate=False``, all ticks render
    as full years.

    Tick placement is delegated to ``matplotlib.dates.YearLocator`` by
    default. Pass ``set_locator=False`` if you have already called
    ``ax.set_xticks(...)`` with a hand-picked tick set you want to keep.
    The "leftmost" tick is detected by comparing tick values against
    the minimum visible tick (not a hardcoded index), so it works for
    both locator-generated and manually-set tick lists.

    Args:
        ax: Axes with a date x-axis.
        abbreviate: Abbreviate all non-leftmost year ticks to ``'YY``.
        set_locator: When True, install ``YearLocator()`` as the major
            locator. Set to False to keep existing ticks.
    """
    if set_locator:
        ax.xaxis.set_major_locator(mdates.YearLocator())

    def _fmt(x: float, _pos) -> str:
        year = mdates.num2date(x).year
        if not abbreviate:
            return str(year)
        x_lo, x_hi = ax.get_xlim()
        ticks = [t for t in ax.get_xticks() if x_lo <= t <= x_hi]
        if ticks and abs(x - min(ticks)) < 1e-6:
            return str(year)
        return f"’{year % 100:02d}"

    ax.xaxis.set_major_formatter(plt.FuncFormatter(_fmt))


def _text_width_fig(
    fig,
    text: str,
    fontproperties: fm.FontProperties,
    *,
    fontsize: float | None = None,
) -> float:
    """Measure rendered width of ``text`` in figure-x fraction (Agg renderer).

    ``fontsize`` overrides the size carried by ``fontproperties`` (or the
    rcParams default) so callers can measure at the exact size they render at.
    """
    artist = fig.text(0, 0, text, fontproperties=fontproperties)
    if fontsize is not None:
        artist.set_fontsize(fontsize)
    try:
        renderer = fig.canvas.get_renderer()
        width_px = artist.get_window_extent(renderer=renderer).width
    finally:
        artist.remove()
    return width_px / (fig.get_figwidth() * fig.dpi)


def _wrap_to_fig_width(
    fig,
    text: str,
    *,
    fontproperties: fm.FontProperties,
    avail_fig_w: float,
) -> str:
    """Greedy word-wrap ``text`` so each line fits ``avail_fig_w`` (figure-x fraction).

    Explicit newlines are preserved: each ``\\n``-separated segment wraps
    independently, so callers can still force semantic breaks (e.g. a
    descriptor's subject / unit split). Words wider than the available
    width are left intact. A single-word last line (a widow) pulls one
    word down from the line above when it still fits. Returns ``text``
    unchanged when the renderer can't measure (non-Agg backends).
    """
    if not text or avail_fig_w <= 0:
        return text
    try:
        fig.canvas.get_renderer()
    except AttributeError:
        # Non-Agg backends can't measure text without drawing — skip the
        # wrap rather than guess. Anything else raising below is a real
        # bug and must surface, not silently disable wrapping.
        return text
    out_lines: list[str] = []
    for segment in text.split("\n"):
        words = segment.split(" ")
        lines: list[str] = []
        line = ""
        for word in words:
            candidate = f"{line} {word}" if line else word
            if line and _text_width_fig(fig, candidate, fontproperties) > avail_fig_w:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
        if len(lines) >= 2 and " " not in lines[-1] and " " in lines[-2]:
            head, _, pulled = lines[-2].rpartition(" ")
            rebalanced = f"{pulled} {lines[-1]}"
            if _text_width_fig(fig, rebalanced, fontproperties) <= avail_fig_w:
                lines[-2], lines[-1] = head, rebalanced
        out_lines.extend(lines)
    return "\n".join(out_lines)


def _wrap_preserve_offsets(text: str, max_chars: int) -> str:
    """Greedy word-wrap that converts inter-word spaces into newlines.

    Length-preserving: a space becomes a ``\\n`` (one char for one char), so the
    character offsets used by URL spans and superscript markers stay valid — the
    superscript renderer counts the newline at the same offset the space held.
    Words longer than ``max_chars`` are left intact (no mid-word breaks).
    """
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    out: list[str] = []
    line_len = 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == " ":
            j = i + 1
            while j < n and text[j] != " ":
                j += 1
            next_word = j - (i + 1)
            if line_len > 0 and line_len + 1 + next_word > max_chars:
                out.append("\n")
                line_len = 0
            else:
                out.append(" ")
                line_len += 1
        else:
            out.append(ch)
            line_len += 1
        i += 1
    return "".join(out)


def verify_layout(fig, *, tolerance: float = 0.005) -> list[str]:
    """Warn when any text artist on ``fig`` extends outside the figure bbox.

    Why this matters: matplotlib's ``savefig(bbox_inches="tight")`` silently
    expands the saved canvas to include any artist that runs past the
    figure edges, which means a broken layout (unwrapped footnotes, an
    over-large legend, a title that overflowed) renders as a much wider or
    taller PNG instead of failing visibly. By the time you notice, you
    have a published figure with the wrong aspect ratio and no error to
    grep.

    This helper walks every text artist on the figure (``fig.texts`` plus
    each axes' tick labels, axis labels, and in-chart text), measures its
    extent in figure coordinates, and emits one ``UserWarning`` per artist
    that crosses ``[tolerance, 1 - tolerance]`` on either axis.

    Auto-called by ``footnotes()`` after rendering. Call it manually
    before ``savefig`` for charts that don't use ``footnotes``.

    Args:
        fig: Figure to inspect.
        tolerance: Fraction of the figure dimension treated as an
            acceptable spill (default 0.5% — accommodates antialiased
            text edges).

    Returns:
        List of warning message strings emitted (for tests / silent-mode
        callers).
    """
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        return []
    inv = fig.transFigure.inverted()

    def _collect():
        for t in fig.texts:
            yield t
        for axes in fig.axes:
            for t in axes.texts:
                yield t
            if axes.title.get_text():
                yield axes.title
            if axes.xaxis.label.get_text():
                yield axes.xaxis.label
            if axes.yaxis.label.get_text():
                yield axes.yaxis.label
            for tl in axes.get_xticklabels() + axes.get_yticklabels():
                if tl.get_text():
                    yield tl
        for leg in fig.legends:
            yield leg

    issued: list[str] = []
    for artist in _collect():
        try:
            bb = artist.get_window_extent(renderer=renderer)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        fig_bb = bb.transformed(inv)
        overflows = []
        if fig_bb.x0 < -tolerance:
            overflows.append(f"left edge at x={fig_bb.x0:.3f}")
        if fig_bb.x1 > 1 + tolerance:
            overflows.append(f"right edge at x={fig_bb.x1:.3f}")
        if fig_bb.y0 < -tolerance:
            overflows.append(f"bottom edge at y={fig_bb.y0:.3f}")
        if fig_bb.y1 > 1 + tolerance:
            overflows.append(f"top edge at y={fig_bb.y1:.3f}")
        if not overflows:
            continue
        # Snippet of the offending text for the warning body.
        text = getattr(artist, "get_text", lambda: "")() or "<legend>"
        snippet = text[:60].replace("\n", " ")
        if len(text) > 60:
            snippet += "…"
        msg = (
            f"graphs.verify_layout: text {snippet!r} extends past the "
            f"figure bounds ({', '.join(overflows)}). "
            f'`savefig(bbox_inches="tight")` will silently expand the '
            f"saved canvas to include it. Fix by wrapping the text, "
            f"shrinking the figure margins, or removing the artist."
        )
        warnings.warn(msg, stacklevel=3)
        issued.append(msg)
    return issued


_LEADING_MARKERS = ("**", "††", "‡‡", "§§", "*", "†", "‡", "§")


def _check_footnote_anchors(fig, notes: tuple[str, ...]) -> None:
    """Warn when a footnote's leading marker isn't anchored elsewhere.

    Walks every existing :class:`~matplotlib.text.Text` artist on ``fig``
    and treats their concatenated text as the universe of possible anchors
    (title, descriptor, axis labels, legend entries, in-chart annotations).
    Notes whose leading marker doesn't appear in that universe trigger a
    ``UserWarning`` so the reader can trace each footnote back to its
    referent.

    Pure introspection — never raises and never modifies the figure.
    """
    if not notes:
        return
    existing = []
    for axes in fig.axes:
        for t in axes.texts:
            existing.append(t.get_text() or "")
        existing.append(axes.title.get_text() or "")
        existing.append(axes.xaxis.label.get_text() or "")
        existing.append(axes.yaxis.label.get_text() or "")
        for tl in axes.get_xticklabels() + axes.get_yticklabels():
            existing.append(tl.get_text() or "")
    for t in fig.texts:
        existing.append(t.get_text() or "")
    # Legend entry texts anchor markers too ("Self-attributed*"). The
    # superscript pass keeps the entry's text (it only zeroes alpha), so the
    # scan sees the marker whether or not finalize has already processed it.
    for legend in _figure_legends(fig):
        for t in legend.get_texts():
            existing.append(t.get_text() or "")
    universe = " ".join(existing)

    for note in notes:
        stripped = note.lstrip()
        for marker in _LEADING_MARKERS:
            if stripped.startswith(marker):
                # The check runs before notes render, so the universe doesn't
                # yet contain this note — a single membership test suffices.
                if marker not in universe:
                    warnings.warn(
                        f"graphs.footnotes: footnote starts with {marker!r} but "
                        f"no matching anchor was found in the title, descriptor, "
                        f"axis labels, legend entries, or in-chart text. Add "
                        f"{marker!r} after a word in the title or descriptor so "
                        f"the reader can trace the note back to its referent.",
                        stacklevel=3,
                    )
                break


def _bottom_band_top(fig) -> float:
    """Top of the bottom band — just under the lowest x-tick label / xlabel.

    Mirrors the ``base_y0`` computation the packed/legacy ``footnotes`` paths
    use: start at the lowest panel baseline, then drop below any x-tick labels
    and the xlabel so a footnote row can't overlap them. Returns a figure-y
    fraction; the stacked layout anchors its bottom-most row a
    ``SOURCE_Y_OFFSET`` below this.
    """
    axes_y0 = [a.get_position().y0 for a in fig.axes]
    base_y0 = min(axes_y0) if axes_y0 else 0.10
    try:
        renderer = fig.canvas.get_renderer()
    except Exception:
        return base_y0
    inv = fig.transFigure.inverted()
    lowest = base_y0
    for a in fig.axes:
        xlabel = a.xaxis.label
        if xlabel.get_text():
            lowest = min(lowest, xlabel.get_window_extent(renderer=renderer).transformed(inv).y0)
        for tl in a.get_xticklabels():
            if not tl.get_text() or not tl.get_visible():
                continue
            lowest = min(lowest, tl.get_window_extent(renderer=renderer).transformed(inv).y0)
    return lowest


def _stack_footnotes(
    fig,
    notes: tuple[str, ...],
    source: str | None,
    *,
    x: float,
    y: float | None,
    max_width_frac: float,
    wrap: bool,
    verify: bool,
) -> None:
    """Render each note on its own line, source on the bottom row, stacked downward.

    The stacked layout — ``footnotes(..., stack=True)``, or the ``stack=None``
    auto default when there is more than one note or a single note that would
    word-wrap: each ``note`` is a distinct entry (a definition line, a caveat)
    that must read as its own row rather than a dense inline run — plus the
    ``source`` line on the bottom-most row. The block anchors its *top* row a
    ``FOOTNOTES_STACK_GAP`` below the x-tick / xlabel band and descends one
    line box per row, so the whole stack sits clear of the axis label and each
    row clear of the next. Each row still word-wraps to the chart width
    (``wrap``), so a long definition that overflows one line adds its own
    continuation rows (and pushes the rows below it further down).

    The band is reserved automatically: every row is wrapped up front and the
    bottom margin grows (:func:`_ensure_bottom_clearance`) until the measured
    stack — wrapped continuation rows included — fits on-figure, so callers do
    not pass ``finalize(footnote_lines=...)``. The exception is a multi-row
    grid (growing its bottom margin post hoc would move the lower row's top
    and detach ``panel_label`` headings): reserve those up front with
    ``finalize(footnote_lines=<total wrapped rows>)``.
    """
    fig.canvas.draw()
    rows = [strip_links(n) for n in notes]
    if source is not None:
        rows.append(strip_links(source))

    fp = fm.FontProperties(family=_get_font_condensed(), weight="light")
    line_h = FOOTNOTE_SIZE_PT * 1.2 / (fig.get_figheight() * 72.0)
    avail_frac = max(0.0, min(max_width_frac, 1.0) - x)

    # Wrap every row up front so the band reservation below sees the true
    # depth — a ~180-char note contributes its wrapped row count, not 1.
    wrapped_rows: list[tuple[str, list, int]] = []
    for text, urls in rows:
        text_w = _text_width_fig(fig, text, fp) if text else 0.0
        per_char = text_w / len(text) if text else 0.0
        max_chars = int(avail_frac / per_char) if per_char > 0 else len(text)
        wrapped = _wrap_preserve_offsets(text, max_chars) if wrap else text
        wrapped_rows.append((wrapped, urls, wrapped.count("\n") + 1))
    total_lines = sum(n_lines for _, _, n_lines in wrapped_rows)

    # Grow the bottom margin until the whole measured stack lands on-figure.
    # ``finalize`` cannot know the wrapped row count (``footnotes`` runs after
    # it), so the reservation happens here — the reason ``footnote_lines`` is
    # no longer needed for single-row figures. Skip when the caller pinned an
    # explicit ``y`` (they own placement then).
    if y is None:
        stack_panel_y0s = [
            a.get_position().y0 for a in fig.axes if a.get_subplotspec() is not None
        ]
        if stack_panel_y0s:
            tick_band = max(0.0, min(stack_panel_y0s) - _bottom_band_top(fig))
            _ensure_bottom_clearance(
                fig,
                depth_below_panels=tick_band
                + FOOTNOTES_STACK_GAP
                + total_lines * line_h,
            )

    band_top = _bottom_band_top(fig)
    # Anchor the TOP row just below the x-tick/xlabel band, then descend — the
    # whole stack stays under the axis label. An explicit ``y`` is honoured as
    # the top row's top.
    top_row_y = y if y is not None else band_top - FOOTNOTES_STACK_GAP

    # Top-to-bottom: the first row (a note) sits highest; the source (last row)
    # is lowest. A row that wrapped to k lines advances the cursor by k line
    # boxes, keeping the row below it clear.
    row_top = top_row_y
    for wrapped, urls, n_lines in wrapped_rows:
        render_text_with_superscripts(
            fig,
            x,
            row_top,
            wrapped,
            fontsize=FOOTNOTE_SIZE_PT,
            fontproperties=fp,
            color=C_SOURCE,
            va="top",
            ha="left",
            url_spans=urls,
        )
        row_top -= n_lines * line_h

    if verify:
        verify_layout(fig)


def _auto_stack(
    fig,
    notes: tuple[str, ...],
    source: str | None,
    *,
    x: float,
    max_width_frac: float,
    wrap: bool,
) -> bool:
    """Resolve ``footnotes(stack=None)``: stacked unless a single short note packs.

    The stacked term-definition layout is the default — more than one note
    always stacks, each definition on its own row. A single note keeps the
    one-row layout only when it genuinely fits on one line: packed on the
    source row (the Economist age-gap pattern) when ``source`` is given, or
    unwrapped at the legacy anchor when it isn't. Both fit tests mirror the
    packed path's own measurements, so ``stack=None`` never resolves to packed
    and then wraps anyway. Falls back to packed when the backend can't measure
    text (non-Agg) — the historical default.
    """
    if len(notes) != 1:
        return len(notes) > 1
    note_clean, _ = strip_links(notes[0])
    if not note_clean:
        return False
    try:
        fig.canvas.draw()
        fp = fm.FontProperties(family=_get_font_condensed(), weight="light")
        note_w = _text_width_fig(fig, note_clean, fp, fontsize=FOOTNOTE_SIZE_PT)
        if source is None:
            # Legacy anchor — stack iff the packed path would word-wrap the
            # note. Mirror its wrap parameters exactly (per-char pitch,
            # symmetric ``x`` margins, ``wrap`` honoured).
            if not wrap:
                return False
            avail = max(0.0, min(max_width_frac, 1.0) - 2 * x)
            per_char = note_w / len(note_clean)
            max_chars = int(avail / per_char) if per_char > 0 else len(note_clean)
            return "\n" in _wrap_preserve_offsets(note_clean, max_chars)
        # Source-aware — stack iff the note can't pack on the source row.
        # Mirrors the packed path's ``notes_fits`` test.
        source_clean, _ = strip_links(source) if source else ("", [])
        src_w = (
            _text_width_fig(fig, source_clean, fp, fontsize=SOURCE_MEASURE_SIZE_PT)
            if source_clean
            else 0.0
        )
        axes_x1 = [a.get_position().x1 for a in fig.axes]
        right_x = max(axes_x1) if axes_x1 else 1.0 - x
        limit = min(right_x, max_width_frac)
        source_wraps = bool(source) and src_w > max(0.0, limit - x)
        fits = not source_wraps and (x + src_w + FOOTNOTES_PACK_GAP + note_w) <= limit
        return not fits
    except Exception:
        return False


def footnotes(
    fig,
    *notes: str,
    source: str | None = None,
    y: float | None = None,
    x: float = 0.02,
    max_width_frac: float = 0.95,
    wrap: bool = True,
    stack: bool | None = None,
    check_anchors: bool = True,
    verify: bool = True,
) -> None:
    """Render footnote strip with optional source-line co-location.

    Joins ``notes`` with two spaces and renders them in IBM Plex Sans
    Condensed at the source line's size (9pt, ``C_SOURCE``).

    Behaviour depends on ``stack`` and whether ``source`` is provided:

    * **Stacked layout** — ``stack=True``, or the ``stack=None`` default when
      there is more than one note or a single note that would word-wrap: each
      ``note`` renders on its OWN line with the ``source`` line on the
      bottom-most row — the whole block sits below the x-tick labels /
      xlabel, every row clear of the axis label and of each other. This is
      the term-definition layout (a set of starred definitions, a list of
      caveats). The bottom band grows to fit the measured stack — wrapped
      continuation rows included — so single-row figures need no
      ``finalize(footnote_lines=...)``; pass ``source=""`` to ``finalize`` so
      it draws no source line. Multi-row grids still reserve up front with
      ``footnote_lines``.
    * **No ``source``** (legacy mode — ``stack=False``, or an auto-packed
      single short note): notes render at ``y`` (defaulting to
      ``min(axes.y0) - 0.045`` — just above the source line drawn by
      ``finalize``). Caller must still pass ``source=...`` to ``finalize``
      to get an attribution line.
    * **With ``source``** (``stack=False``, or an auto-packed single short
      note): notes try to pack on the SAME ROW as the source line,
      right-aligned to ``bbox.x1`` of the widest axes (matches the
      Economist age-gap layout). If the combined source + notes would
      exceed ``max_width_frac`` of the figure width, notes wrap to a row
      ABOVE the source instead. Caller should pass ``source=""`` to
      ``finalize`` to suppress its own source line and avoid duplication.

    Args:
        fig: Figure to draw on.
        *notes: Footnote strings (e.g. ``"*Where at least 50…"``).
        source: Optional source attribution. When provided, ``footnotes``
            owns rendering of both the notes and the source line.
        y: Explicit y in figure coords. When ``None``, the layout picks a
            sensible default just above the source-line band.
        x: Left anchor in figure coords (matches ``finalize(title_x=0.02)``).
        max_width_frac: When ``source`` is provided, packing falls back to
            a stacked layout if source + notes would exceed this fraction
            of the figure width. Defaults to 0.95.
        wrap: When True (default), word-wrap notes that overflow one row
            (offset-preserving, so URL spans and superscript markers stay
            valid). Disable for fixed-width legacy layouts.
        stack: ``None`` (default) picks the layout: more than one note, or a
            single note that would word-wrap, renders stacked (one row per
            note, source on the bottom row); a single note that fits packed
            keeps the one-row layout. ``True`` forces the stacked layout;
            ``False`` forces the packed/legacy layout.
        check_anchors: When True (default), warn if any footnote's leading
            marker (``*``, ``†``, ``‡``, ``§``) isn't found in the title,
            descriptor, axis labels, legend entries (axes and figure-level),
            or any in-chart text.
        verify: When True (default), run :func:`verify_layout` after
            rendering to warn if any text artist has overflowed the figure
            bbox (a silent ``bbox_inches="tight"`` expansion).
    """
    if not notes and not source:
        return
    if check_anchors:
        _check_footnote_anchors(fig, notes)

    if stack is None:
        stack = _auto_stack(
            fig, notes, source, x=x, max_width_frac=max_width_frac, wrap=wrap
        )
    if stack:
        _stack_footnotes(
            fig,
            notes,
            source,
            x=x,
            y=y,
            max_width_frac=max_width_frac,
            wrap=wrap,
            verify=verify,
        )
        return

    fig.canvas.draw()

    # Make sure the panels sit high enough for the source/notes band to land
    # on-figure. Facets (and any chart that draws its source via ``footnotes``)
    # tell ``finalize`` ``source=""``, so its auto-layout reserved no source
    # room; without this the band falls off the bottom. Skip when the caller
    # pinned an explicit ``y`` (they own placement then).
    if y is None:
        _ensure_bottom_clearance(
            fig, depth_below_panels=_footnotes_band_depth(fig, notes, source)
        )

    axes_y0 = [a.get_position().y0 for a in fig.axes]
    axes_x1 = [a.get_position().x1 for a in fig.axes]
    base_y0 = min(axes_y0) if axes_y0 else 0.10
    right_x = max(axes_x1) if axes_x1 else 1.0 - x

    # Drop base_y0 below any x-tick labels or xlabel so footnotes don't
    # overlap them. Mirrors the logic in ``finalize`` for the source line.
    try:
        renderer = fig.canvas.get_renderer()
        lowest_fig_y = base_y0
        for a in fig.axes:
            xlabel = a.xaxis.label
            if xlabel.get_text():
                xlbl_bbox = xlabel.get_window_extent(renderer=renderer)
                lowest_fig_y = min(
                    lowest_fig_y,
                    xlbl_bbox.transformed(fig.transFigure.inverted()).y0,
                )
            for tl in a.get_xticklabels():
                if not tl.get_text() or not tl.get_visible():
                    continue
                tl_bb = tl.get_window_extent(renderer=renderer)
                lowest_fig_y = min(
                    lowest_fig_y,
                    tl_bb.transformed(fig.transFigure.inverted()).y0,
                )
        base_y0 = lowest_fig_y
    except Exception:
        pass

    notes_str = "  ".join(notes) if notes else ""
    fp_notes = fm.FontProperties(family=_get_font_condensed(), weight="light")
    fp_src = fm.FontProperties(family=_get_font_condensed(), weight="light")

    notes_clean, notes_urls = strip_links(notes_str) if notes_str else ("", [])
    source_clean, source_urls = strip_links(source) if source else ("", [])

    def _text_width_frac(text: str, fp, fontsize: float) -> float:
        if not text:
            return 0.0
        renderer = fig.canvas.get_renderer()
        t = fig.text(0, 0, text, fontproperties=fp, fontsize=fontsize)
        bb = t.get_window_extent(renderer=renderer)
        t.remove()
        return bb.width / (fig.get_figwidth() * fig.dpi)

    notes_w = (
        _text_width_frac(notes_clean, fp_notes, FOOTNOTE_SIZE_PT)
        if notes_clean
        else 0.0
    )
    line_h = FOOTNOTE_SIZE_PT * 1.2 / (fig.get_figheight() * 72.0)

    def _wrap_lines(text: str, avail_frac: float, *, text_w: float) -> str:
        """Word-wrap ``text`` to ``avail_frac`` of the figure width (no render).

        ``text_w`` is the rendered single-line width of ``text`` (figure-x
        fraction), used to estimate the per-character pitch. Returns the
        wrapped string so callers can count rows before placing it.
        """
        per_char = text_w / len(text) if text else 0.0
        max_chars = int(avail_frac / per_char) if per_char > 0 else len(text)
        return _wrap_preserve_offsets(text, max_chars) if wrap else text

    def _draw_wrapped(
        text: str,
        urls,
        anchor_y: float,
        avail_frac: float,
        *,
        text_w: float,
        fontproperties=fp_notes,
    ) -> int:
        """Word-wrap ``text`` to ``avail_frac`` of the figure width and stack the
        lines upward, so the bottom line sits at ``anchor_y`` (va='top' baseline).

        ``text_w`` is the rendered single-line width of ``text`` (figure-x
        fraction), used to estimate the per-character pitch — pass the width
        measured for the same font as ``fontproperties``. Returns the number of
        rendered lines so callers can advance their layout cursor past a
        multi-line block.
        """
        wrapped = _wrap_lines(text, avail_frac, text_w=text_w)
        n_lines = wrapped.count("\n") + 1
        render_text_with_superscripts(
            fig,
            x,
            anchor_y + (n_lines - 1) * line_h,
            wrapped,
            fontsize=FOOTNOTE_SIZE_PT,
            fontproperties=fontproperties,
            color=C_SOURCE,
            va="top",
            ha="left",
            url_spans=urls,
        )
        return n_lines

    if source is None:
        # Legacy mode — render notes only at the historical position, wrapped.
        if not notes_str:
            return
        y_pos = y if y is not None else base_y0 - FOOTNOTES_LEGACY_Y_OFFSET
        _draw_wrapped(
            notes_clean,
            notes_urls,
            y_pos,
            max(0.0, min(max_width_frac, 1.0) - 2 * x),
            text_w=notes_w,
        )
        if verify:
            verify_layout(fig)
        return

    # Source-aware mode: render source on its own baseline, pack notes
    # alongside if there is room, otherwise word-wrap them above.
    source_y = y if y is not None else base_y0 - SOURCE_Y_OFFSET

    src_w = _text_width_frac(source_clean, fp_src, SOURCE_MEASURE_SIZE_PT)

    # An over-wide source overflows the figure edge just as an over-wide note
    # would — word-wrap it to the chart width, exactly as the notes wrap. When
    # it fits on one line, render it as-is and try to pack notes alongside.
    source_avail_frac = max(0.0, min(right_x, max_width_frac) - x)
    source_wraps = bool(source) and src_w > source_avail_frac

    # Available room between source's right edge and the chart's right edge,
    # minus a small visual gap. A wrapped (multi-line) source leaves no room to
    # pack notes on its baseline.
    gap = FOOTNOTES_PACK_GAP
    src_right = x + src_w
    notes_fits = (
        notes_clean
        and not source_wraps
        and (src_right + gap + notes_w) <= min(right_x, max_width_frac)
    )

    # When the notes wrap to rows ABOVE the source line, that stack climbs back
    # up toward the x-tick labels. ``base_y0`` already sits just below the
    # labels, so the source line's default ``SOURCE_Y_OFFSET`` gap leaves no
    # room for the rows to stack without overlapping the category labels. Drop
    # the source baseline by the wrapped block's height (notes rows + the wrapped
    # source's own extra rows + the stack gap) so the TOP of the block lands a
    # ``SOURCE_TICK_CLEARANCE`` below ``base_y0`` — clear of the labels — when ``y``
    # is auto-chosen. An explicit ``y`` is honoured as-is.
    notes_wrap_above = bool(notes_clean) and not notes_fits
    if y is None and notes_wrap_above:
        notes_avail_frac = max(0.0, min(right_x, max_width_frac) - x)
        n_note_rows = (
            _wrap_lines(notes_clean, notes_avail_frac, text_w=notes_w).count("\n") + 1
        )
        n_src_rows = (
            _wrap_lines(source_clean, source_avail_frac, text_w=src_w).count("\n") + 1
            if source_wraps
            else 1
        )
        block_h = FOOTNOTES_STACK_GAP + (n_src_rows - 1 + n_note_rows) * line_h
        source_y = min(source_y, base_y0 - SOURCE_TICK_CLEARANCE - block_h)

    # Always draw the source line — wrapped to the figure width when over-wide.
    n_source_lines = 1
    if source_wraps:
        n_source_lines = _draw_wrapped(
            source_clean,
            source_urls,
            source_y,
            source_avail_frac,
            text_w=src_w,
            fontproperties=fp_src,
        )
    elif source:
        render_text_with_superscripts(
            fig,
            x,
            source_y,
            source_clean,
            fontsize=SOURCE_SIZE_PT,
            fontproperties=fp_src,
            color=C_SOURCE,
            va="top",
            ha="left",
            url_spans=source_urls,
        )

    if not notes_clean:
        if verify:
            verify_layout(fig)
        return

    if notes_fits:
        # Same row, right-aligned to the rightmost axes edge.
        render_text_with_superscripts(
            fig,
            right_x,
            source_y,
            notes_clean,
            fontsize=SOURCE_SIZE_PT,
            fontproperties=fp_notes,
            color=C_SOURCE,
            va="top",
            ha="right",
            url_spans=notes_urls,
        )
    else:
        # Too wide for the source row — word-wrap and stack the lines above it.
        # A wrapped source occupies extra lines stacking up from source_y, so
        # lift the notes block clear of them.
        notes_anchor_y = source_y + FOOTNOTES_STACK_GAP + (n_source_lines - 1) * line_h
        _draw_wrapped(
            notes_clean,
            notes_urls,
            notes_anchor_y,
            max(0.0, min(right_x, max_width_frac) - x),
            text_w=notes_w,
        )

    if verify:
        verify_layout(fig)
