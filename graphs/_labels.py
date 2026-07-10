"""Direct line labelling — replaces legends for line charts."""

from __future__ import annotations

import re
import warnings
from collections import defaultdict
from typing import Iterable

import matplotlib.font_manager as fm
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy

from graphs._fonts import _get_font

# Halo colour for label strokes. C_BG is "none" (transparent) under the new
# theme, which would render no halo at all — use white explicitly so labels
# stay readable when they cross gridlines.
_HALO = "#FFFFFF"


def label_lines(
    ax,
    labels: list[str] | None = None,
    *,
    x_offset: int = 6,
    fontsize: int = 9,
    stroke: bool = True,
    min_sep_pct: float = 5.0,
    tick_pad_pct: float = 4.5,
    edge_pull_pct: float = 1.5,
):
    """Label each line at its rightmost point instead of using a legend.

    Visible y-tick rows are treated as fixed dividers. Each label is placed
    in the band between two consecutive ticks (with `tick_pad_pct` padding off
    each tick) so labels can never obscure axis tick text. Within a band,
    labels are spread evenly with at least `min_sep_pct` separation; if the
    band is too narrow for the labels in it, separation shrinks to fit
    without spilling onto the tick rows.

    Args:
        labels: Override list of strings (defaults to line labels).
        x_offset: Horizontal pixel offset from the last data point.
        fontsize: Label font size.
        stroke: White halo behind text to avoid clashing with gridlines.
        min_sep_pct: Minimum label separation as % of y-axis range.
        tick_pad_pct: Minimum gap between any label and a y-tick row,
            as % of y-axis range. Set to 0 to disable tick-avoidance.
        edge_pull_pct: When a line ends exactly at y_lo or y_hi (so its
            label would otherwise sit on top of the 0% / 100% tick text),
            pull the label this many % of the y-range *into* the chart.
            Set to 0 to disable.
    """
    lines = [line for line in ax.get_lines() if not line.get_label().startswith("_")]
    if not lines:
        return

    y_lo, y_hi = ax.get_ylim()
    span = y_hi - y_lo
    min_sep = span * min_sep_pct / 100
    tick_pad = span * tick_pad_pct / 100
    edge_pull = span * edge_pull_pct / 100

    # Visible ticks define band boundaries. The axis limits cap the outer bands.
    yticks = sorted(t for t in ax.get_yticks() if y_lo <= t <= y_hi)
    tick_set = set(yticks)
    edges = [y_lo] + yticks + [y_hi]
    bands: list[tuple[float, float]] = []
    for i in range(len(edges) - 1):
        lo = edges[i] + (tick_pad if edges[i] in tick_set else 0)
        hi = edges[i + 1] - (tick_pad if edges[i + 1] in tick_set else 0)
        if hi > lo:
            bands.append((lo, hi))
    if not bands:  # degenerate: no usable band, fall back to full axis
        bands = [(y_lo, y_hi)]

    chart_center = (y_lo + y_hi) / 2

    def assign_band(y: float) -> tuple[float, float]:
        """Pick the band for a label at `y`.

        Strict containment wins. Otherwise pick the band whose nearest edge
        is closest to `y`; on ties (label sits exactly on a tick boundary),
        pick the band whose centre is closer to the chart centre — so labels
        for lines that end at the axis extremes land *interior* to the chart
        rather than spilling outside the spine.
        """
        for lo, hi in bands:
            if lo <= y <= hi:
                return (lo, hi)

        def edge_dist(b):
            lo, hi = b
            return min(abs(lo - y), abs(hi - y))

        d_min = min(edge_dist(b) for b in bands)
        candidates = [b for b in bands if edge_dist(b) == d_min]
        if len(candidates) == 1:
            return candidates[0]
        return min(candidates, key=lambda b: abs((b[0] + b[1]) / 2 - chart_center))

    items: list[list] = []
    for i, line in enumerate(lines):
        lbl = labels[i] if labels and i < len(labels) else line.get_label()
        y = float(line.get_ydata()[-1])
        # Pull labels that hug the axis extremes into the chart so they don't
        # collide with the 0% / 100% tick text.
        if edge_pull > 0:
            if abs(y - y_hi) < tick_pad:
                y = y_hi - edge_pull - tick_pad
            elif abs(y - y_lo) < tick_pad:
                y = y_lo + edge_pull + tick_pad
        items.append([y, lbl, line, assign_band(y)])

    # Distribute each band's labels evenly inside it, anchored near their mean y.
    by_band: dict[tuple[float, float], list[list]] = defaultdict(list)
    for it in items:
        by_band[it[3]].append(it)

    for (band_lo, band_hi), group in by_band.items():
        group.sort(key=lambda it: it[0])
        n = len(group)
        if n == 1:
            group[0][0] = max(band_lo, min(band_hi, group[0][0]))
            continue
        avail = band_hi - band_lo
        sep = min(min_sep, avail / (n - 1))
        total = (n - 1) * sep
        mean_y = sum(it[0] for it in group) / n
        center = max(band_lo + total / 2, min(band_hi - total / 2, mean_y))
        start = center - total / 2
        for i, it in enumerate(group):
            it[0] = start + i * sep

    path_fx = [pe.withStroke(linewidth=3, foreground=_HALO)] if stroke else []
    annotations = []
    for nudged_y, lbl, line, _ in items:
        ann = ax.annotate(
            lbl,
            xy=(line.get_xdata()[-1], nudged_y),
            xytext=(x_offset, 0),
            textcoords="offset points",
            va="center",
            fontsize=fontsize,
            color=line.get_color(),
            path_effects=path_fx,
            clip_on=False,
            annotation_clip=False,
        )
        annotations.append(ann)

    # Render-pass: detect residual overlaps between labels in pixel space and
    # spread them in y. Necessary because the band-distribution pass works in
    # data coords and can leave labels touching when the band is very thin or
    # when two lines end within a few pixels of each other.
    fig = ax.get_figure()
    try:
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
    except Exception:
        return

    def _bbox(a):
        return a.get_window_extent(renderer=renderer)

    for _ in range(8):
        bboxes = [(_bbox(a), a) for a in annotations]
        bboxes.sort(key=lambda b: b[0].y0)
        moved = False
        for i in range(1, len(bboxes)):
            prev_bb, _ = bboxes[i - 1]
            cur_bb, cur_ann = bboxes[i]
            overlap = prev_bb.y1 - cur_bb.y0
            if overlap > 0:
                # nudge current annotation up by `overlap + 1px`
                shift_px = overlap + 1
                inv = ax.transData.inverted()
                _, y0 = inv.transform((0, 0))
                _, y1 = inv.transform((0, shift_px))
                dy = y1 - y0
                xy = cur_ann.xy
                cur_ann.xy = (xy[0], xy[1] + dy)
                moved = True
        if not moved:
            break

    # Final warning if any label still overlaps a y-tick label in pixel space.
    tick_bboxes = []
    for tl in ax.get_yticklabels():
        if tl.get_text():
            try:
                tick_bboxes.append(tl.get_window_extent(renderer=renderer))
            except Exception:
                pass
    for ann in annotations:
        bb = _bbox(ann)
        for tb in tick_bboxes:
            if bb.overlaps(tb):
                warnings.warn(
                    f"graphs.label_lines: label {ann.get_text()!r} overlaps "
                    "a y-tick label. Consider increasing tick_pad_pct or "
                    "tightening y-limits.",
                    stacklevel=2,
                )
                break


def inset_tick_labels(ax, *, axis: str = "x") -> None:
    """Inset the first and last tick labels so they stay within the chart bounds.

    Standard Economist convention: end labels align to the inside edge of the
    plot area rather than centring on the tick (which would overflow). The
    first label gets ``ha="left"`` so its left edge sits on the first tick;
    the last gets ``ha="right"`` so its right edge sits on the last tick.
    Middle labels stay centred.

    Args:
        ax: Axes whose tick labels should be inset.
        axis: ``"x"`` (default) or ``"y"``.
    """
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")

    getter = ax.get_xticklabels if axis == "x" else ax.get_yticklabels
    labels = list(getter())
    if not labels:
        return
    labels[0].set_ha("left")
    labels[-1].set_ha("right")


_NUMERIC_TICK = re.compile(
    r"""(?x)                    # verbose
    ^
    [\s$£€]*                    # optional currency prefix
    [-−+]?                      # sign (ASCII hyphen or U+2212 minus)
    (?=[\d.])                   # require at least one digit ahead
    [\d,]*                      # integer digits, thousands separators
    (?:\.\d+)?                  # decimal part
    \s*
    (?:[kKmMbBtT]|bn|tn)?       # compact magnitude suffix (format_count/_fmt_decade)
    \s*%?                       # percent unit
    $
    """
)


def _ticks_are_numeric(labels: Iterable[str]) -> bool:
    """True when every label reads as a number (with house units: %, $, k/M/B/T).

    A single non-numeric or multi-line label marks the axis categorical —
    ``y_labels_on_grid`` styling only suits numeric scale labels.
    """
    return all("\n" not in text and _NUMERIC_TICK.match(text.strip()) for text in labels)


def y_labels_on_grid(ax, *, pad_pt: float = 4.0, label_lift_pt: float = 2.5) -> None:
    """Sit y tick labels on top of gridlines that extend under them.

    Standard Economist daily-chart convention: each gridline continues past
    the axes edge into the label gutter, ending flush with the labels'
    common outer edge; the label rests just above its line. Works on
    whichever side the labels sit — right-side labels get rightward
    extensions, left-side labels leftward (e.g. a latitude axis). The bottom
    tick's extension inherits the dark spine / zero-rule stroke when it
    coincides with one, so "0" sits on the rule. When the floor is *not* a
    gridded tick, the bottom baseline is itself extended into the gutter so
    it ends flush with the gridlines rather than at the data edge.

    Call AFTER ``finalize()`` (labels and limits must be final). Native
    tick labels are replaced by figure-stable text artists; the series
    stay clipped at the axes edge — only grid strokes cross into the
    gutter.

    Args:
        ax: Axes styled with the theme's y labels (either side).
        pad_pt: Gap between the axes edge and the labels' near extent,
            in points.
        label_lift_pt: Gap between a label's baseline and the gridline it
            rests on, in points — a little breathing room so glyphs don't
            touch the rule.
    """
    fig = ax.get_figure()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    ticks = [
        (loc, label)
        for loc, label in zip(ax.get_yticks(), ax.get_yticklabels())
        if label.get_text() and label.get_visible()
    ]
    y_lo, y_hi = sorted(ax.get_ylim())
    # The physical floor is whichever bound matplotlib draws at the bottom edge —
    # always ``ylim[0]``, which is the numerical *max* on an inverted axis (e.g. a
    # horizontal bar chart). Using ``y_lo`` here would put the dark baseline stub at
    # the visual top on inverted axes.
    floor_loc = ax.get_ylim()[0]
    ticks = [(loc, label) for loc, label in ticks if y_lo <= loc <= y_hi]
    if not ticks:
        return

    # Categorical axes (bar rows, thermometer categories — anything whose tick
    # text isn't a number) keep their native, tick-centred labels: lifting a
    # category label onto its gridline reads as belonging to the row above,
    # and a multi-line label overlaps it outright. The finalize gate checks
    # y-gridline visibility, but a hand-rolled categorical chart that leaves
    # the y-grid flag on would slip through — guard on the label text itself.
    if not _ticks_are_numeric(label.get_text() for _, label in ticks):
        return

    # Clear any previous application (idempotent re-styling).
    for artist in list(ax.lines) + list(ax.texts):
        if artist.get_gid() == "y-labels-on-grid":
            artist.remove()

    # Which side do the labels sit on? Compare label centres to the axes.
    ax_bbox = ax.get_window_extent(renderer=renderer)
    centres = [
        label.get_window_extent(renderer=renderer).x0
        + label.get_window_extent(renderer=renderer).width / 2
        for _, label in ticks
    ]
    side = (
        "left"
        if sum(centres) / len(centres) < (ax_bbox.x0 + ax_bbox.x1) / 2
        else "right"
    )

    # Common outer edge: pad + widest label, converted to axes-x fraction.
    axes_w_px = ax_bbox.width
    pad_px = pad_pt / 72.0 * fig.dpi
    max_w_px = max(
        label.get_window_extent(renderer=renderer).width for _, label in ticks
    )
    gutter_frac = (pad_px + max_w_px) / axes_w_px
    if side == "right":
        edge_frac, near_frac, text_ha = 1.0 + gutter_frac, 1.0, "right"
    else:
        edge_frac, near_frac, text_ha = -gutter_frac, 0.0, "left"

    gridlines = ax.get_ygridlines()
    grid_by_loc = dict(zip(ax.get_yticks(), gridlines))
    bottom_spine = ax.spines["bottom"]
    trans = ax.get_yaxis_transform(which="grid")
    # Lift labels a hair off their gridline so glyphs don't touch the rule.
    label_trans = offset_copy(trans, fig=fig, y=label_lift_pt, units="points")

    for loc, label in ticks:
        # Stroke style: continue the gridline; at the axes floor, continue
        # the dark baseline instead so "0" sits on the rule. Hidden
        # gridlines (e.g. suppressed edge rules) get no extension.
        grid = grid_by_loc.get(loc)
        if grid is not None and not grid.get_visible():
            grid = None
        color = grid.get_color() if grid is not None else "0.85"
        lw = grid.get_linewidth() if grid is not None else 0.6
        on_baseline = bottom_spine.get_visible() and abs(loc - floor_loc) <= 1e-9 * max(
            1.0, abs(y_hi - y_lo)
        )
        if on_baseline:
            color = bottom_spine.get_edgecolor()
            lw = bottom_spine.get_linewidth()
        if grid is not None or on_baseline:
            ax.add_line(
                plt.Line2D(
                    [near_frac, edge_frac],
                    [loc, loc],
                    transform=trans,
                    color=color,
                    linewidth=lw,
                    solid_capstyle="butt",
                    clip_on=False,
                    zorder=grid.get_zorder() if grid is not None else 0.5,
                    gid="y-labels-on-grid",
                )
            )
        text = ax.text(
            edge_frac,
            loc,
            label.get_text(),
            transform=label_trans,
            ha=text_ha,
            va="bottom",
            fontsize=label.get_fontsize(),
            color=label.get_color(),
            fontfamily=label.get_fontfamily(),
            gid="y-labels-on-grid",
        )
        text.set_clip_on(False)

    # Extend the bottom baseline into the label gutter so it ends flush with
    # the gridlines. When a tick sits on the floor its extension above already
    # carries the dark baseline stroke, so only extend when the floor is bare.
    floor_has_tick = any(
        abs(loc - floor_loc) <= 1e-9 * max(1.0, abs(y_hi - y_lo)) for loc, _ in ticks
    )
    if bottom_spine.get_visible() and not floor_has_tick:
        ax.add_line(
            plt.Line2D(
                [near_frac, edge_frac],
                [floor_loc, floor_loc],
                transform=trans,
                color=bottom_spine.get_edgecolor(),
                linewidth=bottom_spine.get_linewidth(),
                solid_capstyle="butt",
                clip_on=False,
                zorder=bottom_spine.get_zorder(),
                gid="y-labels-on-grid",
            )
        )

    ax.tick_params(axis="y", labelright=False, labelleft=False)


def italicize_labels(
    ax,
    labels: Iterable[str],
    *,
    axis: str = "y",
    fontsize: float = 9,
) -> None:
    """Render the given tick labels in italic IBM Plex Sans.

    Useful when a category axis mixes individuals (upright) with
    organisations/parties (italic), per the Economist convention.

    Args:
        ax: Axes whose tick labels should be restyled.
        labels: Iterable of label strings to italicise. Any tick whose
            text matches one of these strings is restyled; others are
            left alone.
        axis: ``"y"`` (default) or ``"x"``.
        fontsize: Font size in points.
    """
    style_labels(ax, italic=labels, axis=axis, fontsize=fontsize)


def style_labels(
    ax,
    *,
    italic: Iterable[str] = (),
    bold: Iterable[str] = (),
    axis: str = "y",
    fontsize: float = 9,
) -> None:
    """Restyle individual tick labels with italic / bold weight.

    ``set_fontproperties`` replaces the entire font spec, which clobbers
    the colour back to its default. This helper re-applies the tick's
    existing colour after the font swap so labels stay visually uniform.

    Args:
        ax: Axes whose tick labels should be restyled.
        italic: Tick texts to render in italic IBM Plex Sans.
        bold: Tick texts to render in bold weight.
        axis: ``"y"`` (default) or ``"x"``.
        fontsize: Font size in points.
    """
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")

    italic_set = set(italic)
    bold_set = set(bold)
    ticks = ax.get_yticklabels() if axis == "y" else ax.get_xticklabels()
    family = _get_font()
    for tick in ticks:
        text = tick.get_text()
        is_italic = text in italic_set
        is_bold = text in bold_set
        if not (is_italic or is_bold):
            continue
        original_color = tick.get_color()
        fp = fm.FontProperties(
            family=family,
            style="italic" if is_italic else "normal",
            weight="bold" if is_bold else "normal",
            size=fontsize,
        )
        tick.set_fontproperties(fp)
        tick.set_color(original_color)
