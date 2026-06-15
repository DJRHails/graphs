"""Chart finalisation — title stack, source line, panel labels."""

import textwrap
import warnings

import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt

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
AUTO_LAYOUT_LEFT = 0.02  # default left margin for finalize(auto_layout=True)
AUTO_LAYOUT_RIGHT = 0.96  # default right margin
AUTO_LAYOUT_TOP_PAD_PT = 6.0  # breathing room above the title-stack
AUTO_LAYOUT_BOTTOM_MARGIN = 0.020  # breathing room below the source baseline
AUTO_LAYOUT_TICK_RESERVE_PT = 16.0  # reserve for a single row of x-tick labels
AUTO_LAYOUT_MARKER_RESERVE_PT = 2.0  # marker overhang above title cap-height


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
) -> tuple[float, float]:
    """Compute (top_pad, bottom_pad) for ``fig.subplots_adjust``.

    Top pad reserves room for the title-stack drawn in figure coords
    above ``bbox.y1`` (descriptor lines, gap, title lines, marker
    overhang, ``y_start`` padding, plus a small breathing margin).

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
    top_pad = y_start + stack_pt * pt2fig + AUTO_LAYOUT_TOP_PAD_PT * pt2fig

    # Reserve the measured height of the bottom x-tick labels (category names
    # on a vertical bar chart). A measured 0.0 means there are genuinely no
    # bottom labels (line/scatter charts, top-mounted ticks) — reserve nothing
    # so those charts are unaffected. Only fall back to the fixed single-row
    # reserve when the renderer couldn't measure at all (``None``, non-Agg).
    measured_band = _xtick_band_height_fig(fig, ax)
    tick_band = (
        measured_band
        if measured_band is not None
        else AUTO_LAYOUT_TICK_RESERVE_PT * pt2fig
    )

    source_h_fig = SOURCE_SIZE_PT * pt2fig
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
    auto_layout: bool = True,
    footnote_lines: int = 0,
    y_labels: str = "on_grid",
):
    """Add Economist finishing touches to an axes object.

    Title stack (top to bottom)::

        Δ           red delta glyph (or short red rule when marker="rule")
        Title       IBM Plex Sans Bold
        Descriptor  IBM Plex Sans Regular

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
        auto_layout: If True (default), call ``fig.subplots_adjust`` with
            top/bottom/left/right margins sized to fit the title-stack and
            source line. Set False when the caller has already configured
            ``subplots_adjust`` (faceted charts that need explicit
            ``hspace``/``wspace`` control).
        footnote_lines: Extra lines of ``footnotes()`` text below the chart.
            Auto-layout reserves an additional ~7pt-line per footnote row so
            wrapped notes don't clip. Pass the count when calling
            ``footnotes(fig, ...)`` after ``finalize`` with multi-line notes.
        y_labels: ``"on_grid"`` (default) sits numeric y tick labels on
            gridlines that extend under them (``y_labels_on_grid``); applied
            only when the axes has visible y gridlines, so categorical
            charts are unaffected. ``"ticks"`` keeps native tick labels.
    """
    if marker not in ("delta", "rule", "none"):
        raise ValueError(f"marker must be 'delta', 'rule', or 'none', got {marker!r}")
    if y_labels not in ("on_grid", "ticks"):
        raise ValueError(f"y_labels must be 'on_grid' or 'ticks', got {y_labels!r}")
    fig = ax.get_figure()

    # Wrap the title stack to the figure's own width BEFORE pad computation
    # (which counts lines). Explicit "\n" survives — only overflowing lines
    # gain breaks — so the wrap is owned by this figure's geometry, never
    # copied from a reference layout.
    wrap_x0 = (
        title_x
        if title_x is not None
        else (AUTO_LAYOUT_LEFT if auto_layout else ax.get_position().x0)
    )
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

    if auto_layout:
        top_pad, bottom_pad = _compute_auto_pads(
            fig,
            ax,
            title=title,
            descriptor=descriptor,
            source=source,
            marker=marker,
            y_start=y_start,
            footnote_lines=footnote_lines,
        )
        fig.subplots_adjust(
            top=1.0 - top_pad,
            bottom=bottom_pad,
            left=AUTO_LAYOUT_LEFT,
            right=AUTO_LAYOUT_RIGHT,
        )

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

    fig.canvas.draw()
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

    # House default: numeric y labels sit on gridlines that extend under
    # them. Gated on visible y gridlines so categorical axes (bar_h rows,
    # thermometer categories) keep their native labels.
    if y_labels == "on_grid" and any(g.get_visible() for g in ax.get_ygridlines()):
        from graphs._labels import y_labels_on_grid

        y_labels_on_grid(ax)

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


def _text_width_fig(fig, text: str, fontproperties: fm.FontProperties) -> float:
    """Measure rendered width of ``text`` in figure-x fraction (Agg renderer)."""
    artist = fig.text(0, 0, text, fontproperties=fontproperties)
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
    (title, descriptor, axis labels, in-chart annotations). Notes whose
    leading marker doesn't appear in that universe trigger a
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
                        f"axis labels, or in-chart text. Add {marker!r} after a "
                        f"word in the title or descriptor so the reader can "
                        f"trace the note back to its referent.",
                        stacklevel=3,
                    )
                break


def footnotes(
    fig,
    *notes: str,
    source: str | None = None,
    y: float | None = None,
    x: float = 0.02,
    max_width_frac: float = 0.95,
    wrap: bool = True,
    check_anchors: bool = True,
    verify: bool = True,
) -> None:
    """Render footnote strip with optional source-line co-location.

    Joins ``notes`` with two spaces and renders them in IBM Plex Sans
    Condensed at the source line's size (9pt, ``C_SOURCE``).

    Behaviour depends on whether ``source`` is provided:

    * **No ``source``** (legacy mode): notes render at ``y`` (defaulting to
      ``min(axes.y0) - 0.045`` — just above the source line drawn by
      ``finalize``). Caller must still pass ``source=...`` to ``finalize``
      to get an attribution line.
    * **With ``source``**: notes try to pack on the SAME ROW as the source
      line, right-aligned to ``bbox.x1`` of the widest axes (matches the
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
        check_anchors: When True (default), warn if any footnote's leading
            marker (``*``, ``†``, ``‡``, ``§``) isn't found in the title,
            descriptor, axis labels, or any in-chart text.
        verify: When True (default), run :func:`verify_layout` after
            rendering to warn if any text artist has overflowed the figure
            bbox (a silent ``bbox_inches="tight"`` expansion).
    """
    if not notes and not source:
        return
    if check_anchors:
        _check_footnote_anchors(fig, notes)

    fig.canvas.draw()
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
