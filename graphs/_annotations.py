"""Annotation, highlight, and emphasis helpers.

Follows the Economist styleguide's annotation system: callout boxes with a
pale fill, vertical event-period bands, single-point highlight labels, and
the index-chart baseline marker.
"""

from __future__ import annotations

import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from graphs._fonts import _get_font_condensed
from graphs._palette import (
    C_BOX_FILL,
    C_HIGHLIGHT_PANEL,
    C_LABEL,
    C_LABEL_MUTED,
    C_RED,
    C_SPINE,
    C_TEXT,
    PALETTE,
)


def callout(
    ax,
    xy: tuple[float, float],
    text: str,
    *,
    xytext: tuple[float, float] | None = None,
    fontsize: float = 9.0,
    fill: str = C_BOX_FILL,
    edgecolor: str = "none",
    arrow: bool = True,
):
    """Pale-fill text callout box with optional arrow to the data point.

    Styleguide spec: Econ Sans Cnd, fill ``c22.5 k15`` at 100% multiply
    (we use the flat ``#E9EDF0`` web equivalent), 6pt horizontal padding,
    arrow centred on the box edge. Default size is 9pt to match direct
    labels (the print spec's 7.5pt reads too small at daily-chart scale).

    Args:
        xy: Data-coordinate point being annotated.
        xytext: Data-coordinate position for the box centre. If omitted,
            offsets ~30 points up-and-right from ``xy``.
        arrow: Draw a thin connector line from box edge to ``xy``.
    """
    fp = fm.FontProperties(family=_get_font_condensed(), size=fontsize)
    bbox = dict(
        boxstyle="round,pad=0.42,rounding_size=0.05",
        facecolor=fill,
        edgecolor=edgecolor,
        linewidth=0,
    )
    arrowprops = (
        dict(arrowstyle="-", color=C_LABEL_MUTED, lw=0.6, shrinkA=2, shrinkB=2)
        if arrow
        else None
    )
    ax.annotate(
        text,
        xy=xy,
        xytext=xytext if xytext is not None else (20, 14),
        textcoords="offset points" if xytext is None else "data",
        color=C_TEXT,
        ha="left",
        va="center",
        fontproperties=fp,
        bbox=bbox,
        arrowprops=arrowprops,
        zorder=10,
    )


def highlight_panel(
    ax,
    x_start,
    x_end,
    *,
    color: str = C_HIGHLIGHT_PANEL,
    alpha: float = 1.0,
    label: str | None = None,
    label_y: float = 0.97,
):
    """Vertical event-period band behind the data.

    Use the subtle ``C_HIGHLIGHT_PANEL`` tint for web charts; use
    ``C_HIGHLIGHT_PANEL_RED`` only when the highlighted period is the
    chart's main message (styleguide reserves red emphasis).

    Args:
        x_start, x_end: Period bounds in data coordinates.
        label: Optional period label drawn near the top of the band.
        label_y: Vertical position of the label in axes coordinates (0–1).
    """
    ax.axvspan(x_start, x_end, color=color, alpha=alpha, linewidth=0, zorder=0)
    if label:
        ax.text(
            (x_start + x_end) / 2,
            label_y,
            label,
            transform=ax.get_xaxis_transform(),
            ha="center",
            va="top",
            fontsize=9.0,
            color=C_LABEL_MUTED,
            family=_get_font_condensed(),
        )


def highlight_label(
    ax,
    xy: tuple[float, float],
    text: str,
    *,
    color: str | None = None,
    role: str = "primary",
    offset: tuple[float, float] = (6, 0),
):
    """Single-point highlight label on a time-series.

    Two styleguide roles:

    * ``"primary"`` — central to the chart's message. Coloured, medium weight.
    * ``"secondary"`` — FORECAST / ESTIMATE / ADJUSTED. Neutral grey, all
      caps, light 6.5pt.
    """
    if role == "secondary":
        ax.annotate(
            text.upper(),
            xy=xy,
            xytext=offset,
            textcoords="offset points",
            color=C_LABEL_MUTED,
            fontsize=7.5,
            family=_get_font_condensed(),
            fontweight="light",
            ha="left",
            va="center",
        )
    else:
        ax.annotate(
            text,
            xy=xy,
            xytext=offset,
            textcoords="offset points",
            color=color or C_RED,
            fontsize=9.0,
            family=_get_font_condensed(),
            fontweight="medium",
            ha="left",
            va="center",
        )


def index_marker(
    ax,
    x,
    *,
    y: float = 100.0,
    dot_size: float = 25.0,
    rule_color: str = C_RED,
):
    """Mark the indexed point on an index chart.

    Styleguide: 5pt diameter black dot on the indexed point + a 0.5pt red
    horizontal line at the index value spanning the chart. Makes the
    "2015=100" baseline visually unambiguous.

    Args:
        x: Data x-coordinate of the indexed point.
        y: Index value (typically 100). Also where the red rule sits.
        dot_size: matplotlib scatter ``s`` for the black dot.
    """
    ax.axhline(y, color=rule_color, linewidth=0.6, zorder=1)
    ax.scatter([x], [y], s=dot_size, color=C_SPINE, zorder=5, linewidths=0)


def _detect_y_label_side(ax) -> str:
    """Return ``"left"`` or ``"right"`` based on which side carries y-tick labels.

    Uses ``ax.yaxis.get_ticks_position()`` first; falls back to inspecting
    which side's tick labels actually have non-empty text when the position
    is ambiguous (``"default"`` / ``"unknown"``).
    """
    pos = ax.yaxis.get_ticks_position()
    if pos in ("right", "left"):
        return pos
    right_has = any(
        t.get_text() for t in ax.get_yticklabels(which="major", minor=False)
    )
    # ``get_yticklabels`` returns one side; check both via tick objects.
    right_visible = any(
        tick.label2.get_visible() and tick.label2.get_text()
        for tick in ax.yaxis.get_major_ticks()
    )
    left_visible = any(
        tick.label1.get_visible() and tick.label1.get_text()
        for tick in ax.yaxis.get_major_ticks()
    )
    if right_visible and not left_visible:
        return "right"
    if left_visible and not right_visible:
        return "left"
    return "right" if right_has else "left"


def _y_label_anchor(ax) -> tuple[str, float, float] | None:
    """Locate the y-label column from ``y_labels_on_grid`` text artists.

    ``finalize`` replaces the native y-tick labels with figure-stable text
    artists (tagged ``"y-labels-on-grid"``) and hides the originals, which
    defeats :func:`_detect_y_label_side`. When those artists are present this
    reads the column straight off them.

    Returns ``(side, x_fig, floor_fig)`` — the side the labels sit on, the
    column's horizontal centre, and the bottom edge of the lowest label, all
    in figure-fraction coords — or ``None`` when the chart keeps its native
    tick labels.
    """
    fig = ax.get_figure()
    renderer = fig.canvas.get_renderer()
    labels = [
        t for t in ax.texts if t.get_gid() == "y-labels-on-grid" and t.get_text()
    ]
    if not labels:
        return None
    boxes = [t.get_window_extent(renderer=renderer) for t in labels]
    x_px = sum((b.x0 + b.x1) / 2 for b in boxes) / len(boxes)
    floor_px = min(b.y0 for b in boxes)  # bottom edge of the lowest label
    ax_bbox = ax.get_window_extent(renderer=renderer)
    side = "right" if x_px > (ax_bbox.x0 + ax_bbox.x1) / 2 else "left"
    fig_w_px = fig.get_figwidth() * fig.dpi
    fig_h_px = fig.get_figheight() * fig.dpi
    return side, x_px / fig_w_px, floor_px / fig_h_px


def _heartbeat_points(
    cx: float, base: float, half_w: float, amp: float
) -> tuple[list[float], list[float]]:
    """Return ``(xs, ys)`` for a symmetric heartbeat glyph in figure coords.

    Flat lead-in, spike up to the peak, spike down past the baseline to the
    trough, then a matched flat lead-out — centred on ``cx`` with its flat
    baseline at ``base``. ``half_w`` is the half-width and ``amp`` the peak
    height (= trough depth), both already in figure-fraction units.
    """
    xs = [
        cx - half_w,
        cx - 0.50 * half_w,
        cx - 0.25 * half_w,
        cx + 0.25 * half_w,
        cx + 0.50 * half_w,
        cx + half_w,
    ]
    ys = [base, base, base + amp, base - amp, base, base]
    return xs, ys


def broken_axis(
    ax,
    *,
    side: str = "auto",
    x: float | None = None,
    size: float = 16.0,
    axis: str = "y",
):
    """Draw the small heartbeat glyph marking a broken/non-zero baseline.

    Styleguide: a flat → spike-up → spike-down → flat mark placed in the
    y-tick-label column, indicating that the scale doesn't start at zero.
    Valid on line, thermometer, and scatter charts. **Never** use on
    bar/column charts — switch to a thermometer instead.

    By default the mark auto-aligns under the y-tick-label column (detected
    from the on-grid labels ``finalize`` lays down) and sits just above the
    bottom spine — or just below it when the lowest label rests on the
    baseline. Pass ``side="left"``/``"right"`` to force the column, or ``x=``
    to anchor at a specific data x-coordinate (overrides ``side``).

    Args:
        side: ``"auto"`` (default), ``"left"``, or ``"right"``. Y-axis only.
        x: Explicit x-axis position (data coords) for the mark.
            Overrides ``side`` when set.
        size: Width of the heartbeat glyph in points.
        axis: ``"y"`` (default), ``"x"``, or ``"both"``. Selects which axes
            get the heartbeat mark — the y-axis mark sits in the tick-label
            column, the x-axis mark on the bottom spine near the origin. Use
            ``"both"`` when both axes have a truncated origin.
    """
    if axis not in ("x", "y", "both"):
        raise ValueError(f"axis must be 'x', 'y', or 'both'; got {axis!r}")

    fig = ax.get_figure()

    # Defer placement until first draw so we see the final tick layout
    # (e.g. ``finalize`` calls ``tick_right`` after this helper).
    state = {"y_line": None, "x_line": None}

    # Clearance from the corner (in points) so the squiggle clears tick marks.
    _CORNER_CLEAR_PT = 7.0

    def _place(_event=None):
        fig_w_px = fig.get_figwidth() * fig.dpi
        fig_h_px = fig.get_figheight() * fig.dpi
        bbox = ax.get_position()
        y_lo = bbox.y0
        # Match the mark stroke to the spine it interrupts.
        spine_lw = ax.spines["bottom"].get_linewidth()
        pt = fig.dpi / 72.0
        half_w = (size / 4) * pt / fig_w_px  # narrow: total width ≈ size/2
        amp = (size * 0.16) * pt / fig_h_px  # peak height (= trough depth)
        gap = 2.0 * pt / fig_h_px

        # ---- y-axis break mark ----
        # A heartbeat glyph — flat, spike up, spike down, flat — drawn across
        # the (implied) y-axis in the tick-label column. It marks the broken
        # vertical scale beside the numbers it qualifies, in the label colour,
        # and stays clear of the bottom spine so the x-axis never looks like
        # the broken one. An explicit ``x=`` or ``side=`` overrides the
        # auto-detected column.
        if axis in ("y", "both"):
            anchor = _y_label_anchor(ax) if (x is None and side == "auto") else None
            label_floor = None
            if x is not None:
                resolved = "left"  # explicit x: left-anchored unless caller picks right
                x_fig = ax.transData.transform((x, ax.get_ylim()[0]))[0] / fig_w_px
            elif anchor is not None:
                resolved, x_fig, label_floor = anchor  # centre on the on-grid column
            else:
                resolved = _detect_y_label_side(ax) if side == "auto" else side
                x_data = ax.get_xlim()[1] if resolved == "right" else ax.get_xlim()[0]
                x_fig = ax.transData.transform((x_data, ax.get_ylim()[0]))[0] / fig_w_px
            if axis == "both":  # push clear of the corner the x-mark occupies
                shift = (_CORNER_CLEAR_PT * pt) / fig_w_px
                x_fig += shift if resolved == "right" else -shift

            # Rest just above the spine; but if the lowest label sits on the
            # baseline (no room above), hang it just below the spine instead.
            base = y_lo + gap + 0.7 * amp  # trough clears the spine by ``gap``
            margin = 1.5 * pt / fig_h_px
            if label_floor is not None and base + amp > label_floor - margin:
                base = y_lo - gap - amp
            xs, ys = _heartbeat_points(x_fig, base, half_w, amp)

            line = state["y_line"]
            if line is None:
                line = plt.Line2D(
                    xs,
                    ys,
                    transform=fig.transFigure,
                    color=C_LABEL,
                    linewidth=spine_lw,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                    clip_on=False,
                )
                fig.add_artist(line)
                state["y_line"] = line
            else:
                line.set_data(xs, ys)

        # ---- x-axis break mark ----
        # The same heartbeat, sitting on the bottom spine just right of the
        # bottom-left corner, marking a truncated x-origin.
        if axis in ("x", "both"):
            x_data_x = ax.get_xlim()[0]
            x_fig_x = ax.transData.transform((x_data_x, ax.get_ylim()[0]))[0] / fig_w_px
            x_fig_x += (_CORNER_CLEAR_PT * pt) / fig_w_px  # clear the corner
            xs2, ys2 = _heartbeat_points(x_fig_x, y_lo, half_w, amp)
            line2 = state["x_line"]
            if line2 is None:
                line2 = plt.Line2D(
                    xs2,
                    ys2,
                    transform=fig.transFigure,
                    color=C_SPINE,
                    linewidth=spine_lw,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                    clip_on=False,
                )
                fig.add_artist(line2)
                state["x_line"] = line2
            else:
                line2.set_data(xs2, ys2)

    fig.canvas.mpl_connect("draw_event", _place)


def _draw_arrow_label(
    fig,
    *,
    arrow_xy: tuple[float, float],
    arrow: str,
    text: str,
    color: str,
    fontsize: float,
    bold: bool,
    placement: str,
    gap: float,
    va: str,
    transform=None,
) -> None:
    """Render an arrow glyph + adjacent text label as a pair.

    Shared primitive behind ``threshold_arrows`` and ``direction_label``.
    The arrow is drawn at ``arrow_xy`` first; the label is then placed
    just past the arrow's measured bounding box so the gap between them
    is constant regardless of glyph width.

    Args:
        fig: Owning figure.
        arrow_xy: Position of the arrow glyph in ``transform`` coords.
        arrow: Glyph string (``"↑"``/``"↓"``/``"←"``/``"→"``).
        text: Label rendered next to the arrow.
        color: Colour for both arrow and label.
        fontsize: Base label font size; the arrow renders at +1pt when bold.
        bold: Render arrow + label bold (and arrow +1pt).
        placement: ``"before"`` puts the arrow before the text in reading
            order (left for ``↑``/``↓``/``→``, right for ``←``).
            ``"after"`` reverses that.
        gap: Spacing between arrow and label, in the transform's units.
        va: Vertical alignment for both arrow and label.
        transform: Coordinate transform. Defaults to ``fig.transFigure``.
    """
    if placement not in ("before", "after"):
        raise ValueError(f"placement must be 'before' or 'after'; got {placement!r}")
    tf = transform if transform is not None else fig.transFigure
    arrow_fontsize = fontsize + 1.0 if bold else fontsize
    weight = "bold" if bold else "normal"
    # ``before`` means arrow precedes label in reading order, so the label
    # sits to the right of the arrow (ha=left). ``after`` puts it to the
    # left (ha=right). For left-pointing arrows the semantics flip so the
    # arrow visually trails the text it modifies.
    label_to_right = placement == "before"
    arrow_ha = "left" if label_to_right else "right"
    label_ha = "left" if label_to_right else "right"
    arrow_artist = fig.text(
        arrow_xy[0],
        arrow_xy[1],
        arrow,
        color=color,
        fontsize=arrow_fontsize,
        fontweight=weight,
        va=va,
        ha=arrow_ha,
        transform=tf,
    )
    bb = arrow_artist.get_window_extent(
        renderer=fig.canvas.get_renderer()
    ).transformed(tf.inverted())
    if label_to_right:
        label_x = bb.x1 + gap
    else:
        label_x = bb.x0 - gap
    fig.text(
        label_x,
        arrow_xy[1],
        text,
        color=color,
        fontsize=fontsize,
        fontweight=weight,
        va=va,
        ha=label_ha,
        transform=tf,
    )


def direction_label(
    ax,
    text: str,
    xy: tuple[float, float],
    *,
    arrow: str = "↑",
    color: str | None = None,
    fontsize: float = 9.0,
    bold: bool = True,
    placement: str = "before",
) -> None:
    """Render a one-sided directional cue (e.g. "↑ Older husband").

    Same typographic conventions as ``threshold_arrows``: bold arrow glyph at
    +1pt, bold label, configurable colour. Position is axes-fraction so the
    cue moves with the chart on resize.

    Args:
        ax: Axes hosting the cue.
        text: Label rendered next to the arrow.
        xy: Position in axes-fraction coords (0..1, 0..1).
        arrow: Glyph — ``"↑"``, ``"↓"``, ``"←"``, or ``"→"``.
        color: Defaults to ``C_LABEL_MUTED`` for neutral cues.
        fontsize: Label font size; arrow renders at +1pt when bold.
        bold: Render arrow + label bold.
        placement: ``"before"`` puts the arrow before the text (default).
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    _draw_arrow_label(
        fig,
        arrow_xy=xy,
        arrow=arrow,
        text=text,
        color=color if color is not None else C_LABEL_MUTED,
        fontsize=fontsize,
        bold=bold,
        placement=placement,
        gap=0.005,
        va="center",
        transform=ax.transAxes,
    )


def threshold_arrows(
    ax,
    threshold: float,
    *,
    left_text: str,
    right_text: str,
    left_color: str | None = None,
    right_color: str | None = None,
    y: float | None = None,
    axis: str = "x",
    fontsize: float = 9.0,
    gap: float = 0.005,
    pad: float = 0.040,
    bold: bool = True,
) -> None:
    """Render a pair of directional labels straddling a threshold value.

    Draws ``left_text`` (typically the negative/unfavourable label) to the
    left/below the threshold with a trailing arrow pointing toward its half,
    and ``right_text`` to the right/above with a leading arrow. Used wherever
    a chart has a meaningful midpoint or break-even line (e.g. an
    affordability ratio of 1, a zero-balance axis, a 50% vote share).

    The labels are placed in figure coordinates just outside the plotting
    area so they survive layout shifts during ``finalize``. Call this helper
    **after** ``finalize`` so the axis position is settled.

    Args:
        ax: Axes hosting the threshold.
        threshold: Data-coordinate value the labels straddle.
        left_text: Label rendered to the left/below; an "<-" arrow is appended.
        right_text: Label rendered to the right/above; a "->" arrow is prepended.
        left_color: Colour for ``left_text``. Defaults to ``PALETTE["red"]``.
        right_color: Colour for ``right_text``. Defaults to ``C_LABEL_MUTED``.
        y: Position in figure coordinates. Defaults to ``pad`` above the
            top of the axes (or to the right of the axes when ``axis="y"``).
        axis: ``"x"`` if ``threshold`` is an x-value (labels are placed
            horizontally above the axes), ``"y"`` if it is a y-value (labels
            are placed vertically to the right of the axes).
        fontsize: Font size for both labels.
        gap: Horizontal/vertical gap between each label and the threshold
            line, in figure coordinates.
        pad: Distance from the axes edge to the label baseline, in figure
            coordinates.
        bold: Render the directional arrow glyph in bold and ~1pt larger
            than the label text. Defaults to True for stronger visibility.
            Set to False to draw arrow + label at uniform weight.
    """
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y'; got {axis!r}")

    fig = ax.get_figure()
    fig.canvas.draw()
    bbox = ax.get_position()

    left_c = left_color if left_color is not None else PALETTE["red"]
    right_c = right_color if right_color is not None else C_LABEL_MUTED

    if axis == "x":
        x_disp = ax.transData.transform((threshold, 0))[0]
        anchor = fig.transFigure.inverted().transform((x_disp, 0))[0]
        baseline = bbox.y1 + pad if y is None else y
        # Left side: "← left_text" reads right-to-left, so arrow comes after
        # the label in DOM order (placement="after" with "←").
        _draw_arrow_label(
            fig,
            arrow_xy=(anchor - gap, baseline),
            arrow="←",
            text=left_text,
            color=left_c,
            fontsize=fontsize,
            bold=bold,
            placement="after",
            gap=gap,
            va="bottom",
        )
        _draw_arrow_label(
            fig,
            arrow_xy=(anchor + gap, baseline),
            arrow="→",
            text=right_text,
            color=right_c,
            fontsize=fontsize,
            bold=bold,
            placement="before",
            gap=gap,
            va="bottom",
        )
    else:
        y_disp = ax.transData.transform((0, threshold))[1]
        anchor = fig.transFigure.inverted().transform((0, y_disp))[1]
        baseline = bbox.x1 + pad if y is None else y
        _draw_arrow_label(
            fig,
            arrow_xy=(baseline, anchor - gap),
            arrow="↓",
            text=left_text,
            color=left_c,
            fontsize=fontsize,
            bold=bold,
            placement="before",
            gap=gap,
            va="top",
        )
        _draw_arrow_label(
            fig,
            arrow_xy=(baseline, anchor + gap),
            arrow="↑",
            text=right_text,
            color=right_c,
            fontsize=fontsize,
            bold=bold,
            placement="before",
            gap=gap,
            va="bottom",
        )


def number_box(
    ax,
    xy: tuple[float, float],
    n: int | str,
    *,
    size: float = 14.0,
    fontsize: float = 7.5,
):
    """Numbered cross-reference box (e.g. linking running text to chart points)."""
    fp = fm.FontProperties(family=_get_font_condensed(), size=fontsize, weight="bold")
    box = mpatches.FancyBboxPatch(
        (xy[0] - size / 2, xy[1] - size / 2),
        size,
        size,
        boxstyle="round,pad=0,rounding_size=2",
        transform=ax.transData,
        facecolor=C_BOX_FILL,
        edgecolor="none",
        zorder=10,
    )
    ax.add_patch(box)
    ax.text(
        xy[0],
        xy[1],
        str(n),
        ha="center",
        va="center",
        color=C_TEXT,
        zorder=11,
        fontproperties=fp,
    )
