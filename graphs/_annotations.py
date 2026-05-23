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
    fontsize: float = 7.5,
    fill: str = C_BOX_FILL,
    edgecolor: str = "none",
    arrow: bool = True,
):
    """Pale-fill text callout box with optional arrow to the data point.

    Styleguide spec: Econ Sans Cnd reg 7.5/9.5pt, fill ``c22.5 k15`` at 100%
    multiply (we use the flat ``#E9EDF0`` web equivalent), 6pt horizontal
    padding, arrow centred on the box edge.

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
            fontsize=7.5,
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
            fontsize=6.5,
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
            fontsize=8.5,
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


def broken_axis(
    ax,
    *,
    side: str = "auto",
    x: float | None = None,
    size: float = 10.0,
    axis: str = "y",
):
    """Draw the small squiggle(s) marking a broken/non-zero baseline.

    Styleguide: small zig-zag stroke placed just outside the plotting area on
    the relevant axis, indicating that the scale doesn't start at zero. Valid
    on line, thermometer, and scatter charts. **Never** use on bar/column
    charts — switch to a thermometer instead.

    By default the y-axis squiggle is placed next to the y-tick-labels column.
    With ``y_axis_right=True`` (our default) that's the right edge; otherwise
    the left. Pass ``side="left"``/``"right"`` to force, or ``x=`` to anchor
    at a specific data x-coordinate (overrides ``side``) — applies to the
    y-axis squiggle only.

    Args:
        side: ``"auto"`` (default), ``"left"``, or ``"right"``. Y-axis only.
        x: Explicit x-axis position (data coords) for the y-axis squiggle.
            Overrides ``side`` when set.
        size: Width in points.
        axis: ``"y"`` (default), ``"x"``, or ``"both"``. Selects which axes
            get a squiggle. Use ``"both"`` when both axes have a truncated
            origin (e.g. brexit: years start mid-2016 and y starts ~36%).
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

        # ---- y-axis squiggle ----
        # When ``axis="y"`` alone (legacy default for index charts) keep the
        # historical horizontal zig-zag sitting on the bottom spine. When
        # ``axis="both"`` the y-axis squiggle becomes a vertical zig-zag
        # running up the y-axis, so it visually pairs with a perpendicular
        # x-axis squiggle on the bottom spine.
        if axis in ("y", "both"):
            if x is None:
                # Place the y-squiggle on whichever side carries the y-tick
                # labels — the squiggle visually annotates the broken scale
                # next to the numbers it's qualifying. Caller can override
                # with ``side="left"``/``"right"``.
                resolved = _detect_y_label_side(ax) if side == "auto" else side
                x_lim = ax.get_xlim()
                x_data = x_lim[1] if resolved == "right" else x_lim[0]
            else:
                resolved = (
                    "left"  # explicit x: assume left-anchored unless caller picks right
                )
                x_data = x
            x_disp = ax.transData.transform((x_data, ax.get_ylim()[0]))[0]
            x_fig = x_disp / fig_w_px
            # When both squiggles are drawn, push the y-axis one further out
            # so it clears the corner tick mark (the x-axis squiggle takes
            # the spot immediately above the data origin).
            if axis == "both":
                shift = (_CORNER_CLEAR_PT / 72.0) * fig.dpi / fig_w_px
                if resolved == "right":
                    x_fig += shift
                else:
                    x_fig -= shift

            if axis == "both":
                # Vertical zig-zag: oscillate x, ascend y. Sits above the
                # bottom-left corner running up along the y-axis line.
                amp_x = (3.0 / 72.0) * fig.dpi / fig_w_px
                half_y = (size / 2) / fig_h_px
                y_mid = y_lo + half_y + (2.0 / 72.0) * fig.dpi / fig_h_px
                ys = [
                    y_mid - half_y,
                    y_mid - half_y / 3,
                    y_mid + half_y / 3,
                    y_mid + half_y,
                ]
                xs = [x_fig - amp_x, x_fig + amp_x, x_fig - amp_x, x_fig + amp_x]
            else:
                # Legacy horizontal zig-zag on the bottom spine.
                half = (size / 2) / fig_w_px
                amp = 0.006  # vertical half-amplitude in figure coords
                y_mid = y_lo + 0.002
                xs = [x_fig - half, x_fig - half / 3, x_fig + half / 3, x_fig + half]
                ys = [y_mid - amp, y_mid + amp, y_mid - amp, y_mid + amp]

            line = state["y_line"]
            if line is None:
                line = plt.Line2D(
                    xs,
                    ys,
                    transform=fig.transFigure,
                    color=C_SPINE,
                    linewidth=1.0,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                    clip_on=False,
                )
                fig.add_artist(line)
                state["y_line"] = line
            else:
                line.set_data(xs, ys)

        # ---- x-axis squiggle (horizontal zig-zag sitting on the bottom spine) ----
        if axis in ("x", "both"):
            # Anchor on the data x-axis (left edge), then nudge right so it sits
            # between the y-axis line and the leftmost data point.
            x_lim = ax.get_xlim()
            x_data_x = x_lim[0]
            x_disp_x = ax.transData.transform((x_data_x, ax.get_ylim()[0]))[0]
            x_fig_x = x_disp_x / fig_w_px
            # Nudge right of the corner so it doesn't collide with the y-axis squiggle.
            x_shift = (_CORNER_CLEAR_PT / 72.0) * fig.dpi / fig_w_px
            x_fig_x += x_shift
            # Horizontal zig-zag: vary x along the spine, oscillate y vertically.
            half_x = (size / 2) / fig_w_px
            # amp in y direction; convert points to figure-y fraction
            amp_y = (3.0 / 72.0) * fig.dpi / fig_h_px
            y_mid_x = y_lo
            xs2 = [
                x_fig_x - half_x,
                x_fig_x - half_x / 3,
                x_fig_x + half_x / 3,
                x_fig_x + half_x,
            ]
            ys2 = [y_mid_x - amp_y, y_mid_x + amp_y, y_mid_x - amp_y, y_mid_x + amp_y]
            line2 = state["x_line"]
            if line2 is None:
                line2 = plt.Line2D(
                    xs2,
                    ys2,
                    transform=fig.transFigure,
                    color=C_SPINE,
                    linewidth=1.0,
                    solid_capstyle="round",
                    solid_joinstyle="round",
                    clip_on=False,
                )
                fig.add_artist(line2)
                state["x_line"] = line2
            else:
                line2.set_data(xs2, ys2)

    fig.canvas.mpl_connect("draw_event", _place)


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
    fontsize: float = 8.5,
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

    arrow_fontsize = fontsize + 1.0 if bold else fontsize
    arrow_weight = "bold" if bold else "normal"
    text_weight = "bold" if bold else "normal"

    if axis == "x":
        x_disp = ax.transData.transform((threshold, 0))[0]
        anchor = fig.transFigure.inverted().transform((x_disp, 0))[0]
        baseline = bbox.y1 + pad if y is None else y
        # Render arrow glyph separately so it can be bolder than the label
        # while still aligning to the same baseline.
        arrow_left = fig.text(
            anchor - gap,
            baseline,
            "←",
            color=left_c,
            fontsize=arrow_fontsize,
            fontweight=arrow_weight,
            va="bottom",
            ha="right",
        )
        arrow_left_bb = arrow_left.get_window_extent(
            renderer=fig.canvas.get_renderer()
        ).transformed(fig.transFigure.inverted())
        fig.text(
            arrow_left_bb.x0 - gap,
            baseline,
            left_text,
            color=left_c,
            fontsize=fontsize,
            fontweight=text_weight,
            va="bottom",
            ha="right",
        )
        arrow_right = fig.text(
            anchor + gap,
            baseline,
            "→",
            color=right_c,
            fontsize=arrow_fontsize,
            fontweight=arrow_weight,
            va="bottom",
            ha="left",
        )
        arrow_right_bb = arrow_right.get_window_extent(
            renderer=fig.canvas.get_renderer()
        ).transformed(fig.transFigure.inverted())
        fig.text(
            arrow_right_bb.x1 + gap,
            baseline,
            right_text,
            color=right_c,
            fontsize=fontsize,
            fontweight=text_weight,
            va="bottom",
            ha="left",
        )
    else:
        y_disp = ax.transData.transform((0, threshold))[1]
        anchor = fig.transFigure.inverted().transform((0, y_disp))[1]
        baseline = bbox.x1 + pad if y is None else y
        arrow_down = fig.text(
            baseline,
            anchor - gap,
            "↓",
            color=left_c,
            fontsize=arrow_fontsize,
            fontweight=arrow_weight,
            va="top",
            ha="left",
        )
        arrow_down_bb = arrow_down.get_window_extent(
            renderer=fig.canvas.get_renderer()
        ).transformed(fig.transFigure.inverted())
        fig.text(
            arrow_down_bb.x1 + gap,
            anchor - gap,
            left_text,
            color=left_c,
            fontsize=fontsize,
            fontweight=text_weight,
            va="top",
            ha="left",
        )
        arrow_up = fig.text(
            baseline,
            anchor + gap,
            "↑",
            color=right_c,
            fontsize=arrow_fontsize,
            fontweight=arrow_weight,
            va="bottom",
            ha="left",
        )
        arrow_up_bb = arrow_up.get_window_extent(
            renderer=fig.canvas.get_renderer()
        ).transformed(fig.transFigure.inverted())
        fig.text(
            arrow_up_bb.x1 + gap,
            anchor + gap,
            right_text,
            color=right_c,
            fontsize=fontsize,
            fontweight=text_weight,
            va="bottom",
            ha="left",
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
