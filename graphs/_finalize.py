"""Chart finalisation — title stack, source line, panel labels."""

import textwrap
import warnings

import matplotlib.dates as mdates
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from graphs._fonts import _get_font, _get_font_condensed
from graphs._palette import C_LABEL_MUTED, C_RED, C_SOURCE, C_SPINE, C_TEXT


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

    _check_x_monotonic(ax)
    if autoscale_y:
        _autoscale_y(ax)

    if y_axis_right:
        ax.yaxis.set_label_position("right")
        ax.yaxis.tick_right()
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(False)

    # Preserve any larger pad set by chart helpers (e.g. bar_h sizes pad
    # to clear the widest left-edge label). Only fall back to the 4pt
    # default when the existing pad is smaller.
    current_pad = ax.yaxis.get_major_ticks()[0].get_pad() if ax.yaxis.get_major_ticks() else 0
    ax.yaxis.set_tick_params(pad=max(current_pad, 4), labelsize=9)
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
    line_gap = 3.5 * pt2fig
    rule_gap = 6.0 * pt2fig
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
            y_cursor = highest_fig_y + 6.0 * pt2fig
    except Exception:
        pass

    if descriptor:
        n_desc_lines = descriptor.count("\n") + 1
        fp_desc = fm.FontProperties(family=_get_font_condensed(), weight="normal")
        fig.text(
            tx,
            y_cursor,
            descriptor,
            transform=fig.transFigure,
            fontsize=9.5,
            fontproperties=fp_desc,
            color=C_SPINE,
            va="bottom",
            ha="left",
            linespacing=1.20,
        )
        # Descriptor line box ≈ 9.5pt × 1.20 ≈ 11.4pt for each line.
        y_cursor += 11.4 * pt2fig * n_desc_lines + line_gap

    if title:
        n_title_lines = title.count("\n") + 1
        fp = fm.FontProperties(family=_get_font(), weight=700)
        fig.text(
            tx,
            y_cursor,
            title,
            transform=fig.transFigure,
            fontsize=12,
            fontproperties=fp,
            color=C_SPINE,
            va="bottom",
            ha="left",
            linespacing=1.15,
        )
        # 12pt bold title line box ≈ 14pt; account for explicit \n wraps.
        y_cursor += 14.0 * pt2fig * n_title_lines + rule_gap

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
        fp_src = fm.FontProperties(family=_get_font_condensed(), weight="light")
        fig.text(
            tx,
            source_y,
            source,
            transform=fig.transFigure,
            fontsize=7.5,
            fontproperties=fp_src,
            color=C_SOURCE,
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


def y_axis_label(
    ax,
    text: str,
    *,
    unit: str | None = None,
    side: str = "right",
    width_frac: float = 0.5,
    fontsize: float = 8.5,
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
    line_h = fontsize * 1.2 * pt2fig
    n_text_lines = wrapped.count("\n") + 1
    y_text = bbox.y1 + 0.005
    if unit:
        y_text += line_h  # leave room below for the unit line

    fig.text(
        x,
        y_text,
        wrapped,
        transform=fig.transFigure,
        fontsize=fontsize,
        fontproperties=fp,
        color=color if color is not None else C_SPINE,
        va="bottom",
        ha=ha,
        linespacing=1.2,
    )

    if unit:
        # Anchor the unit line directly under the wrapped text block.
        y_unit = y_text - line_h * n_text_lines
        fig.text(
            x,
            y_unit,
            unit,
            transform=fig.transFigure,
            fontsize=fontsize,
            fontproperties=fp,
            color=unit_color if unit_color is not None else C_LABEL_MUTED,
            va="bottom",
            ha=ha,
            linespacing=1.2,
        )


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


def footnotes(
    fig,
    *notes: str,
    source: str | None = None,
    y: float | None = None,
    x: float = 0.02,
    max_width_frac: float = 0.95,
) -> None:
    """Render footnote strip with optional source-line co-location.

    Joins ``notes`` with two spaces and renders them in IBM Plex Sans
    Condensed Light 7pt ``C_LABEL_MUTED``.

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
    """
    if not notes and not source:
        return

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

    if source is None:
        # Legacy mode — render notes only at the historical position.
        if not notes_str:
            return
        y_pos = y if y is not None else base_y0 - 0.045
        fig.text(
            x,
            y_pos,
            notes_str,
            transform=fig.transFigure,
            fontsize=7,
            fontproperties=fp_notes,
            color=C_SOURCE,
            va="top",
            ha="left",
        )
        return

    # Source-aware mode: render source on its own baseline, pack notes
    # alongside if there is room, otherwise wrap them one row above.
    source_y = y if y is not None else base_y0 - 0.06

    def _text_width_frac(text: str, fp, fontsize: float) -> float:
        if not text:
            return 0.0
        renderer = fig.canvas.get_renderer()
        t = fig.text(0, 0, text, fontproperties=fp, fontsize=fontsize)
        bb = t.get_window_extent(renderer=renderer)
        t.remove()
        return bb.width / (fig.get_figwidth() * fig.dpi)

    src_w = _text_width_frac(source, fp_src, 7.5)
    notes_w = _text_width_frac(notes_str, fp_notes, 7) if notes_str else 0.0

    # Available room between source's right edge and the chart's right edge,
    # minus a small visual gap.
    gap = 0.02
    src_right = x + src_w
    notes_fits = (
        notes_str
        and (src_right + gap + notes_w) <= min(right_x, max_width_frac)
    )

    # Always draw the source line.
    if source:
        fig.text(
            x,
            source_y,
            source,
            transform=fig.transFigure,
            fontsize=7.5,
            fontproperties=fp_src,
            color=C_SOURCE,
            va="top",
            ha="left",
        )

    if not notes_str:
        return

    if notes_fits:
        # Same row, right-aligned to the rightmost axes edge.
        fig.text(
            right_x,
            source_y,
            notes_str,
            transform=fig.transFigure,
            fontsize=7,
            fontproperties=fp_notes,
            color=C_SOURCE,
            va="top",
            ha="right",
        )
    else:
        # Wrap above the source line.
        fig.text(
            x,
            source_y + 0.022,
            notes_str,
            transform=fig.transFigure,
            fontsize=7,
            fontproperties=fp_notes,
            color=C_SOURCE,
            va="top",
            ha="left",
        )
