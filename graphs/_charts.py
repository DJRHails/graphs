"""Reusable Economist-style chart helpers."""

from __future__ import annotations

import warnings
from typing import Sequence

from graphs._palette import (
    C_CI,
    C_GRID,
    C_LABEL,
    C_LABEL_MUTED,
    C_OTHER,
    C_RED,
    C_SPINE,
    PALETTE,
    colors,
    cycle_for,
)

_SIDES = ("left", "right", "top", "bottom")
_OPPOSITE = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}

# Styleguide working ceiling for categorical comparisons (thermometer, bubble,
# pie/doughnut). Beyond this, the styleguide says "you should have a rethink."
_CATEGORY_CEILING = 4


def ci_fill(ax, x, y_lower, y_upper, *, color: str | None = None, alpha: float = 0.20):
    """Fill a confidence-interval band.

    By default uses the Economist salmon (#f5c5b8) at full opacity — the
    legacy behaviour, fine for charts with a single series. When a colour is
    provided, draws a semi-transparent fill in that colour so the band visibly
    matches its line. Pair with `ax.plot(..., color=col)` and pass the same
    `col` here.

    Args:
        color: Fill colour. Pass the matching line colour to colour-match.
        alpha: Opacity when `color` is given. Ignored when `color` is None.
    """
    if color is None:
        ax.fill_between(x, y_lower, y_upper, color=C_CI, linewidth=0, zorder=1)
    else:
        ax.fill_between(
            x, y_lower, y_upper, color=color, alpha=alpha, linewidth=0, zorder=1
        )


def bar_h(
    ax,
    categories: Sequence[str],
    values: Sequence[float],
    *,
    color: str | None = None,
    highlight_max: bool = True,
):
    """Horizontal bar chart in Economist style.

    Category labels sit right-aligned to the left of the bars.
    The highest-value bar is highlighted in red.
    """
    color = color or colors[1]
    bars = ax.barh(categories, values, color=color, height=0.6, zorder=2)

    if highlight_max and values:
        idx, _ = max(enumerate(values), key=lambda x: x[1])
        bars[idx].set_color(C_RED)

    ax.spines[["top", "left", "right", "bottom"]].set_visible(False)
    ax.set_yticks(range(len(categories)))
    # Labels sit in a left-edge column, flush-left. With ha="left" the
    # label's left edge is at (tick_x - pad) in points, so pad must clear
    # the widest label plus a small gutter to the bars.
    ax.set_yticklabels(categories, ha="left", fontsize=9, color=C_LABEL)
    longest = max((len(c) for c in categories), default=0)
    pad_pts = longest * 9 * 0.55 + 8  # ~0.55em per char at 9pt + 8pt gutter
    ax.yaxis.set_tick_params(length=0, pad=pad_pts)
    # Economist convention for horizontal bars: x-axis on top.
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.xaxis.set_tick_params(labelsize=9, length=3.5, direction="out")
    ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=0)
    ax.grid(axis="y", visible=False)
    return ax


def dumbbell(
    ax,
    categories: Sequence[str],
    values_start: Sequence[float],
    values_end: Sequence[float],
    *,
    label_start: str = "Start",
    label_end: str = "End",
    color_start: str | None = None,
    color_end: str | None = None,
):
    """Dumbbell (dot-and-line) chart for showing change between two periods.

    Scatter handles are stored on ``ax._dumbbell_handles`` so you
    can pass them to ``fig.legend()`` afterwards.
    """
    color_start = color_start or PALETTE["red"]
    color_end = color_end or PALETTE["blue"]

    ax.hlines(
        y=categories,
        xmin=values_start,
        xmax=values_end,
        color=C_LABEL,
        linewidth=2,
        alpha=0.6,
        zorder=2,
        label="_nolegend_",
    )

    s1 = ax.scatter(
        values_start,
        categories,
        s=80,
        color=color_start,
        zorder=4,
        label=label_start,
    )
    s2 = ax.scatter(
        values_end,
        categories,
        s=80,
        color=color_end,
        zorder=4,
        label=label_end,
    )

    ax.spines[["top", "left", "right"]].set_visible(False)
    ax.spines["bottom"].set_color(C_SPINE)
    ax.yaxis.set_tick_params(length=0, pad=6)
    ax.xaxis.set_tick_params(labelsize=9, length=3.5, direction="out")
    ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=0)
    ax.grid(axis="y", visible=False)

    ax._dumbbell_handles = [s1, s2]
    return ax


# ---------------------------------------------------------------------------
# Scatter — three dot variants from the styleguide
# ---------------------------------------------------------------------------
def scatter_standard(ax, x, y, *, color: str | None = None, size: float = 16.0):
    """General-trend scatter: 4px width equivalent, 50% opacity, no stroke."""
    color = color or cycle_for("scatter")[0]
    return ax.scatter(x, y, s=size, color=color, alpha=0.5, linewidths=0, zorder=3)


def scatter_highlight(ax, x, y, *, color: str | None = None, size: float = 16.0):
    """Outlier / labelled-point scatter: 4px width, 100% opacity, no stroke."""
    color = color or C_RED
    return ax.scatter(x, y, s=size, color=color, alpha=1.0, linewidths=0, zorder=4)


def scatter_category(
    ax, x, y, *, color: str | None = None, size: float = 64.0, stroke: float = 0.3
):
    """Bubble-chart dot: 50% fill, 0.3px stroke — keeps overlap legible."""
    color = color or cycle_for("bubble")[0]
    return ax.scatter(
        x,
        y,
        s=size,
        color=color,
        alpha=0.5,
        edgecolors=color,
        linewidths=stroke,
        zorder=3,
    )


def color_axis(
    ax,
    side: str,
    color: str,
    *,
    color_spine: bool = False,
    width: float = 1.0,
    tick_length: float = 3.5,
    spine: bool = True,
    ticks: bool = True,
) -> None:
    """Colour tick labels on one axis (and optionally the spine + ticks).

    Used for double-axis charts where each scale carries its own colour
    (Economist convention). By default ONLY the tick labels (numbers) take
    the series colour — the spine and tick marks stay in the default
    dark-grey so the chart frame reads as a single coherent baseline. Set
    ``color_spine=True`` to colour the spine and tick marks as well.

    The opposite spine is hidden in either mode to avoid a competing
    baseline on twin-axis charts.

    Args:
        ax: Axes to restyle.
        side: One of ``"left"``, ``"right"``, ``"top"``, ``"bottom"``.
        color: Colour to apply to the tick labels (and, if ``color_spine``,
            to the spine and tick marks).
        color_spine: If True, colour the spine line and tick marks too.
            Default False — only the labels are coloured.
        width: Spine width in points (only used when ``color_spine``).
        tick_length: Tick mark length in points.
        spine: If False, hide the spine on ``side`` entirely (gridlines-only
            charts). Default True.
        ticks: If False, suppress the tick marks on ``side`` (labels remain).
            Default True.
    """
    if side not in _SIDES:
        raise ValueError(f"side must be one of {_SIDES}, got {side!r}")

    axis_name = "y" if side in ("left", "right") else "x"
    effective_tick_length = tick_length if ticks else 0
    if color_spine:
        ax.tick_params(
            axis=axis_name,
            which="both",
            colors=color,
            labelcolor=color,
            length=effective_tick_length,
        )
        if spine:
            ax.spines[side].set_visible(True)
            ax.spines[side].set_color(color)
            ax.spines[side].set_linewidth(width)
        else:
            ax.spines[side].set_visible(False)
    else:
        ax.tick_params(
            axis=axis_name,
            which="both",
            labelcolor=color,
            length=effective_tick_length,
        )
        ax.spines[side].set_visible(spine)
    ax.spines[_OPPOSITE[side]].set_visible(False)


def right_axis(ax, *, hide_right_spine: bool = True) -> None:
    """Move y-axis labels/ticks to the right and hide top/left spines.

    Standard Economist convention applied per panel in multi-panel layouts
    where ``finalize`` runs only on one axes but every panel needs the same
    treatment. For single-panel charts, prefer ``finalize(y_axis_right=True)``.

    Args:
        ax: Axes to restyle.
        hide_right_spine: When True (default), hide the right spine too —
            matches the convention used by ``finalize`` and the panel
            examples (eu_balance, us_trade).
    """
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    if hide_right_spine:
        ax.spines[["top", "left", "right"]].set_visible(False)
    else:
        ax.spines[["top", "left"]].set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(C_SPINE)


def trend_line(ax, x, y, *, color: str = C_SPINE):
    """Dashed trend line: 1px stroke, 3-on/1-off dash pattern."""
    return ax.plot(x, y, color=color, linewidth=1.0, linestyle=(0, (3, 1)), zorder=2)


def smoothed_line(
    ax,
    x,
    y,
    *,
    color: str,
    label: str | None = None,
    band_alpha: float = 0.12,
    scatter_alpha: float = 0.32,
    scatter_size: float = 14.0,
    line_width: float = 1.8,
    window: int = 7,
    band_sigma: float = 1.0,
):
    """Three-layer Economist time-series: scatter + soft CI band + smoothed line.

    Renders, in order of zorder:
      1. faint scatter of the raw points (``scatter_alpha`` opacity);
      2. soft ±``band_sigma`` × rolling-std confidence band (``band_alpha``);
      3. smoothed trend line through the rolling mean.

    All three layers share ``color`` so the eye reads them as one series. Use
    once per series — pair with another call in a contrasting colour for the
    classic two-series Economist look (e.g. dark slate + accent red).

    Args:
        ax: Axes to draw on.
        x: 1-D sequence of x values (numeric or date-like).
        y: 1-D sequence of raw y values matching ``x``.
        color: Colour for all three layers.
        label: Optional label attached to the line (for legends).
        band_alpha: Opacity of the CI band fill (default 0.12).
        scatter_alpha: Opacity of the raw scatter dots (default 0.32).
        scatter_size: Marker area for the raw scatter.
        line_width: Stroke width of the smoothed line.
        window: Rolling-window size for the smoother / band (must be ≥ 3).
        band_sigma: Multiplier on the rolling std for the band half-width.

    Returns:
        The Line2D for the smoothed trend (handy for legend handles).
    """
    import numpy as np

    if window < 3:
        raise ValueError(f"window must be >= 3, got {window}")

    x_arr = np.asarray(x)
    y_arr = np.asarray(y, dtype=float)
    n = len(y_arr)
    if n != len(x_arr):
        raise ValueError(f"x and y length mismatch: {len(x_arr)} vs {n}")

    # Centred rolling mean / std via cumulative-sum trick, with edge handling
    # that shrinks the window symmetrically near the boundaries (avoids the
    # NaN gutters that pandas.rolling would leave).
    half = window // 2
    mean = np.empty(n)
    std = np.empty(n)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        window_slice = y_arr[lo:hi]
        mean[i] = window_slice.mean()
        std[i] = window_slice.std()

    band_half = band_sigma * std
    ax.fill_between(
        x_arr,
        mean - band_half,
        mean + band_half,
        color=color,
        alpha=band_alpha,
        linewidth=0,
        zorder=1,
    )
    ax.scatter(
        x_arr,
        y_arr,
        s=scatter_size,
        color=color,
        alpha=scatter_alpha,
        linewidths=0,
        zorder=2,
    )
    (line,) = ax.plot(
        x_arr,
        mean,
        color=color,
        linewidth=line_width,
        label=label,
        solid_capstyle="round",
        zorder=3,
    )
    return line


# ---------------------------------------------------------------------------
# Thermometer — tick-and-dot chart, ranked category comparison
# ---------------------------------------------------------------------------
def thermometer(
    ax,
    categories: Sequence[str],
    values: Sequence[Sequence[float]],
    *,
    series_labels: Sequence[str] | None = None,
    colors_: Sequence[str] | None = None,
    dot: bool = True,
):
    """Tick-and-dot chart — one row per category, points along a horizontal axis.

    Use for ranked category comparisons. Styleguide ceiling is 4 series; this
    helper warns above that. ``dot=True`` uses the "dot terminal" variant
    (filled circles); ``dot=False`` uses short vertical ticks.

    Args:
        categories: Row labels.
        values: One sequence of floats per category. Each sub-sequence is one
            series of values across the same x-axis.
        series_labels: Optional legend labels per series.
        colors_: Override the series colour order (defaults to ``cycle_for("thermometer")``).
    """
    n_series = len(values[0]) if values else 0
    if n_series > _CATEGORY_CEILING:
        warnings.warn(
            f"graphs.thermometer: {n_series} series exceeds the styleguide "
            f"ceiling of {_CATEGORY_CEILING}. Consider a different chart type.",
            stacklevel=2,
        )

    series_colors = list(colors_) if colors_ else cycle_for("thermometer")
    y_positions = list(range(len(categories)))

    for i, category_values in enumerate(values):
        for s_idx, v in enumerate(category_values):
            col = series_colors[s_idx % len(series_colors)]
            if dot:
                ax.scatter([v], [i], s=70, color=col, linewidths=0, zorder=3)
            else:
                ax.vlines(v, i - 0.18, i + 0.18, color=col, linewidth=2.0, zorder=3)

    # Pale baseline tick per row to anchor the eye.
    for yp in y_positions:
        ax.axhline(yp, color=C_GRID, linewidth=0.5, zorder=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(categories, ha="right", fontsize=9, color=C_LABEL)
    ax.yaxis.set_tick_params(length=0, pad=6)
    ax.xaxis.set_tick_params(labelsize=9, length=3.5, direction="out")
    ax.spines[["top", "left", "right"]].set_visible(False)
    ax.spines["bottom"].set_color(C_SPINE)
    ax.grid(axis="x", color=C_GRID, linewidth=0.6, zorder=0)
    ax.grid(axis="y", visible=False)
    ax.set_ylim(-0.5, len(categories) - 0.5)
    ax.invert_yaxis()

    if series_labels:
        handles = []
        for i, lbl in enumerate(series_labels):
            col = series_colors[i % len(series_colors)]
            (h,) = ax.plot([], [], "o", color=col, label=lbl, linestyle="")
            handles.append(h)
        ax._thermometer_handles = handles

    return ax


# ---------------------------------------------------------------------------
# Bump chart — smooth-curve rank movement across columns / time points
# ---------------------------------------------------------------------------
def bump_chart(
    ax,
    ranks: dict[str, list[int]],
    *,
    highlight: Sequence[str] | None = None,
    colors: dict[str, str] | None = None,  # noqa: A002 — shadows module-level palette
    smoothing: float = 0.3,
    dot_size: float = 30.0,
    faded_alpha: float = 0.15,
    faded_color: str = C_OTHER,
    x_labels: Sequence[str] | None = None,
    x_labels_top: bool = False,
    right_labels: bool = False,
    right_label_format: str = "{rank} {name}",
    right_label_fontsize: float = 9.0,
    right_label_color: str | None = None,
    highlight_halo: bool = True,
    highlight_halo_color: str = "white",
    highlight_halo_extra_width: float = 2.0,
    aspect: float | None = None,
) -> dict[str, str]:
    """Bump chart — smooth-curve movement of rankings across columns.

    Visualises how a set of series (countries, teams, categories…) trade
    ranks across a sequence of columns / time points. Each series is rendered
    as a smooth monotone curve through (column_index, rank). Highlighted
    series take their accent colour and end in a terminal dot; non-highlighted
    series form a faded backdrop so the eye latches onto the story without
    losing context.

    Top-half highlights default to blues/greys/navy; bottom-half highlights
    default to reds, mirroring the Economist convention for "rising" vs
    "falling" groups. Override per-series via ``colors``.

    Args:
        ranks: Mapping ``series_name → list[int]`` of ranks per column
            (1 = top). All lists must share the same length.
        highlight: Series names to render in full colour. ``None`` highlights
            every series.
        colors: Explicit per-series colours. Missing entries fall back to a
            position-based default (top half blue/grey/navy, bottom half reds).
        smoothing: 0 ≈ straight lines, 1 ≈ very smooth Bezier-like curves.
            Implemented via Pchip resampling density — the interpolator itself
            is monotone so curves never overshoot.
        dot_size: Marker size for the terminal dot.
        faded_alpha: Opacity of non-highlighted series in the backdrop.
        faded_color: Stroke colour for the backdrop series.
        x_labels: Optional labels for each column (e.g. ``["2018", ..., "25"]``).
            Length must match ``n_cols``. When omitted, ticks render as numeric
            column indices (existing default behaviour).
        x_labels_top: Also render ``x_labels`` along the top of the axes
            (Economist convention when both ends carry rank annotations).
        right_labels: Render the final rank + name for each highlighted series
            at the right edge in the matching colour, replacing the need for
            a legend.
        right_label_format: Python format string for the right-edge label.
            Available fields: ``rank``, ``name``.
        right_label_fontsize: Font size for the right-edge labels.
        right_label_color: Override colour for right-edge labels. When ``None``
            (default), each label inherits its line's colour, with the
            default top-palette grey/slate replaced by ``C_SPINE`` so labels
            read sharply against the page.
        highlight_halo: Draw a white outline behind highlighted lines so
            crossings between them (and other lines) read clearly.
        highlight_halo_color: Halo colour (default white).
        highlight_halo_extra_width: Pixels added to the line's linewidth to
            form the halo stroke.
        aspect: Optional width/height ratio. When provided, sets the axes
            box aspect via :meth:`Axes.set_box_aspect` (``height/width``).
            E.g. ``aspect=0.85`` makes the chart slightly taller than wide,
            matching ranking-heavy bump charts.

    Returns:
        Mapping ``series_name → colour`` for every highlighted series. Callers
        can reuse the assignments for matching annotations or legends.
    """
    import numpy as np
    from matplotlib import patheffects
    from scipy.interpolate import PchipInterpolator

    if not ranks:
        return

    n_cols = len(next(iter(ranks.values())))
    if any(len(v) != n_cols for v in ranks.values()):
        raise ValueError("All rank sequences must share the same length")

    n_series = len(ranks)
    half = n_series // 2

    # Highlight defaults — everything is highlighted unless caller restricts.
    highlight_set = set(highlight) if highlight is not None else set(ranks.keys())

    # Default colour assignment: top-half blues/slate/navy, bottom-half reds.
    # Use near-black + deep navy for the non-blue slots — C_LABEL (#3F5661)
    # and PALETTE["grey"] (#758D99) read washed out at 2 px against white.
    top_palette = [PALETTE["blue"], PALETTE["cyan"], C_SPINE, "#003F5C", "#2A3A45"]
    bot_palette = [PALETTE["red"], "#A8201A", "#E55D3A", "#7A1F18", "#D04B3D"]
    colors = dict(colors) if colors else {}

    # Resample density encodes the smoothing knob (rounded to ≥2 segments).
    points_per_segment = max(8, int(6 + smoothing * 80))
    xs_dense = np.linspace(0, n_cols - 1, (n_cols - 1) * points_per_segment + 1)
    x_grid = np.arange(n_cols)

    # Backdrop first so highlighted series sit on top.
    for name, series in ranks.items():
        if name in highlight_set:
            continue
        interp = PchipInterpolator(x_grid, np.asarray(series, dtype=float))
        ax.plot(
            xs_dense,
            interp(xs_dense),
            color=faded_color,
            linewidth=2,
            alpha=faded_alpha,
            zorder=2,
            solid_capstyle="round",
        )

    # Highlighted series — sort by final rank so top-of-stack determines colour bucket.
    highlighted = [(name, ranks[name]) for name in ranks if name in highlight_set]
    final_sorted = sorted(highlighted, key=lambda kv: kv[1][-1])
    top_idx = 0
    bot_idx = 0
    assigned_colors: dict[str, str] = {}
    for name, series in final_sorted:
        ending_rank = series[-1]
        if name in colors:
            col = colors[name]
        elif ending_rank <= half:
            col = top_palette[top_idx % len(top_palette)]
            top_idx += 1
        else:
            col = bot_palette[bot_idx % len(bot_palette)]
            bot_idx += 1
        assigned_colors[name] = col

        interp = PchipInterpolator(x_grid, np.asarray(series, dtype=float))
        line_kwargs = dict(
            color=col,
            linewidth=2.0,
            alpha=0.95,
            zorder=4,
            solid_capstyle="round",
        )
        if highlight_halo:
            line_kwargs["path_effects"] = [
                patheffects.withStroke(
                    linewidth=2.0 + highlight_halo_extra_width,
                    foreground=highlight_halo_color,
                ),
            ]
        ax.plot(xs_dense, interp(xs_dense), **line_kwargs)
        ax.scatter(
            [n_cols - 1],
            [series[-1]],
            s=dot_size,
            color=col,
            zorder=5,
            linewidths=0,
        )

    # Axis cosmetics — emphasise the lines, not the numeric ranks.
    # Pad x-limits when right-edge labels are on, to make room for the text.
    right_pad = 0.18 if right_labels else 0.05
    ax.set_xlim(-0.05, n_cols - 1 + right_pad)
    ax.set_ylim(n_series + 0.5, 0.5)  # inverted: rank 1 at top
    ax.set_xticks(x_grid)
    if x_labels is not None:
        if len(x_labels) != n_cols:
            raise ValueError(
                f"x_labels length {len(x_labels)} does not match n_cols {n_cols}"
            )
        ax.set_xticklabels(list(x_labels))
    ax.set_yticks(range(1, n_series + 1))
    ax.set_yticklabels([])
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9, length=3.5, direction="out", color=C_SPINE)
    if x_labels_top and x_labels is not None:
        # Mirror the column labels along the top of the chart. We use a
        # secondary axis so the labels share the same x-data coordinates.
        sec = ax.secondary_xaxis("top")
        sec.set_xticks(x_grid)
        sec.set_xticklabels(list(x_labels))
        sec.tick_params(
            axis="x", labelsize=9, length=3.5, direction="out", color=C_SPINE
        )
        sec.spines["top"].set_visible(False)
    for side in ("top", "left", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.grid(False)
    # Light vertical gridlines at each column so the eye can anchor moments.
    # Drawn after grid(False) so they aren't wiped, and at low zorder so
    # they sit under all curves and dots.
    for x in x_grid:
        ax.axvline(x, color=C_GRID, linewidth=0.6, zorder=0, alpha=0.8)

    if right_labels:
        # Place rank+name to the right of the terminal dot, coloured to match.
        # Resolve collisions in pixel space after the initial draw.
        annotations = []
        for name, series in final_sorted:
            line_col = assigned_colors[name]
            if right_label_color is not None:
                label_col = right_label_color
            else:
                # Inherit the line colour, but bump muted slates to C_SPINE
                # so labels read sharply (lines can stay slate without the
                # text reading as washed-out grey).
                label_col = (
                    C_SPINE
                    if line_col in {C_LABEL, C_LABEL_MUTED, PALETTE["grey"]}
                    else line_col
                )
            text = right_label_format.format(rank=series[-1], name=name)
            ann = ax.annotate(
                text,
                xy=(n_cols - 1, series[-1]),
                xytext=(8, 0),
                textcoords="offset points",
                va="center",
                ha="left",
                fontsize=right_label_fontsize,
                color=label_col,
                clip_on=False,
                annotation_clip=False,
                zorder=6,
            )
            annotations.append(ann)
        _spread_annotations_y(ax, annotations)

    if aspect is not None:
        # box_aspect is height/width — invert so the caller-facing `aspect`
        # reads as the more intuitive width/height ratio.
        ax.set_box_aspect(1.0 / aspect)

    return assigned_colors


def threshold_lollipop(
    ax,
    categories: Sequence[str],
    values: Sequence[float],
    *,
    threshold: float = 1.0,
    below_color: str | None = None,
    above_color: str | None = None,
    line_color: str | None = None,
    dot_size: float = 60.0,
) -> None:
    """Horizontal lollipop with a fixed threshold reference line.

    Each category gets a leader line from its dot to ``threshold``. Dots
    below the threshold render in ``below_color`` (default
    ``PALETTE["red"]``); dots at or above render in ``above_color``
    (default ``C_LABEL_MUTED``). Useful for affordability / share-of-X /
    relative-index charts where the story is "which side of the line is
    this on, and by how much?".

    The x-axis is moved to the top (Economist horizontal convention) and
    light vertical gridlines are drawn so the eye can pick out the
    threshold and the tick stops. Caller is responsible for x-scale
    (e.g. ``ax.set_xscale("log")``) and tick placement.

    Args:
        categories: Row labels, drawn top-to-bottom in the order given.
        values: One numeric value per category.
        threshold: Centreline value where leader lines terminate.
        below_color: Dot colour when ``value < threshold``.
        above_color: Dot colour when ``value >= threshold``.
        line_color: Leader-line colour (default ``C_LABEL_MUTED``).
        dot_size: Marker area for the dots.
    """
    if len(categories) != len(values):
        raise ValueError(
            f"categories and values length mismatch: {len(categories)} vs {len(values)}"
        )

    below = below_color or PALETTE["red"]
    above = above_color or C_LABEL_MUTED
    line = line_color or C_LABEL_MUTED

    y_positions = list(range(len(categories)))
    dot_colors = [below if v < threshold else above for v in values]

    for y, v, col in zip(y_positions, values, dot_colors):
        ax.hlines(
            y=y,
            xmin=min(v, threshold),
            xmax=max(v, threshold),
            color=line,
            linewidth=1.0,
            alpha=0.75,
            zorder=2,
        )
        ax.scatter([v], [y], s=dot_size, color=col, linewidths=0, zorder=4)

    ax.axvline(threshold, color=C_SPINE, linewidth=0.8, zorder=1)

    ax.set_yticks(y_positions)
    ax.set_yticklabels(categories, ha="right", fontsize=9, color=C_LABEL)
    ax.yaxis.set_tick_params(length=0, pad=6)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.xaxis.set_tick_params(labelsize=9, length=3.5, direction="out")
    ax.spines[["top", "left", "right", "bottom"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="x", which="major", color=C_GRID, linewidth=0.6, zorder=0)
    ax.grid(axis="y", visible=False)
    ax.set_ylim(len(categories) - 0.5, -0.5)
    return ax


def _spread_annotations_y(ax, annotations) -> None:
    """Nudge annotations apart vertically so they don't overlap in pixel space.

    Sorts annotations by current y-pixel position and walks them in order,
    pushing any that overlap their predecessor down by ``overlap + 1px``.
    Used by ``bump_chart`` for right-edge labels that sit on top of each
    other when multiple curves end at adjacent ranks.
    """
    fig = ax.get_figure()
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        return

    inv = ax.transData.inverted()
    for _ in range(8):
        bboxes = sorted(
            ((a.get_window_extent(renderer=renderer), a) for a in annotations),
            key=lambda b: b[0].y0,
        )
        moved = False
        for i in range(1, len(bboxes)):
            prev_bb, _ = bboxes[i - 1]
            cur_bb, cur_ann = bboxes[i]
            overlap = prev_bb.y1 - cur_bb.y0
            if overlap > 0:
                _, y0 = inv.transform((0, 0))
                _, y1 = inv.transform((0, overlap + 1))
                dy = y1 - y0
                xy = cur_ann.xy
                cur_ann.xy = (xy[0], xy[1] + dy)
                moved = True
        if not moved:
            break
