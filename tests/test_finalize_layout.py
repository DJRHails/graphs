"""Auto-layout bottom-margin: x-tick labels must not overlap footnotes."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, footnotes, set_theme, top_legend
from graphs._finalize import _xtick_band_height_fig


@pytest.fixture(autouse=True)
def _theme():
    set_theme()


def _bottom_band_top(fig, *, below: float = 0.30) -> float:
    """Highest y1 of any bottom-band text artist (source / footnotes)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    top = 0.0
    for t in fig.texts:
        bb = t.get_window_extent(renderer=renderer).transformed(inv)
        if bb.y1 < below and t.get_text().strip():
            top = max(top, bb.y1)
    return top


def _xtick_band_y0(fig, ax) -> float:
    """Lowest y0 of the visible bottom x-tick labels."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    y0 = 1.0
    for tl in ax.get_xticklabels():
        if not tl.get_text():
            continue
        y0 = min(y0, tl.get_window_extent(renderer=renderer).transformed(inv).y0)
    return y0


def test_category_labels_do_not_overlap_multiline_footnotes():
    """Vertical bars with x-category labels + 2-line footnotes + top_legend.

    The category labels (``forced`` / ``calibrated`` / ``recall-biased``)
    must sit ABOVE the footnote band — no caller-side ``subplots_adjust``.
    """
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    cats = ["forced", "calibrated", "recall-biased"]
    xs, ys, hs = [], [], []
    for c in cats:
        for s, v in (("A", 0.6), ("B", 0.45)):
            xs.append(c)
            hs.append(s)
            ys.append(v)
    # Plain matplotlib grouped bars (seaborn not a test dependency).
    import numpy as np

    idx = np.arange(len(cats))
    ax.bar(idx - 0.2, [0.6, 0.3, 0.8], width=0.4, label="A")
    ax.bar(idx + 0.2, [0.45, 0.27, 0.69], width=0.4, label="B")
    ax.set_xticks(idx)
    ax.set_xticklabels(cats)
    ax.set_ylim(0, 1)
    handles, labels = ax.get_legend_handles_labels()
    top_legend(fig, handles, labels)

    finalize(
        ax,
        title="False-positive rate by monitor regime",
        descriptor="Share of benign transcripts flagged\n% of sampled traffic",
        footnote_lines=2,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(
            fig,
            "*Forced regime asks a yes/no harm question.",
            "†Calibrated thresholds tuned on a held-out split.",
            source="Source: Touchstone cross-harm eval, 2026",
        )

    tick_y0 = _xtick_band_y0(fig, ax)
    foot_top = _bottom_band_top(fig)
    assert foot_top < tick_y0, (
        f"footnote band top {foot_top:.4f} overlaps the x-tick labels "
        f"(lowest tick y0 {tick_y0:.4f})"
    )
    overflow = [str(w.message) for w in caught if "verify_layout" in str(w.message)]
    assert not overflow, f"verify_layout flagged an overflow: {overflow}"
    plt.close(fig)


def test_xtick_band_height_zero_without_bottom_labels():
    """Line charts with hidden x-ticks measure ~0 band — no extra reserve."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1, 2], [0, 1, 0])
    ax.set_xticks([])
    assert _xtick_band_height_fig(fig, ax) == 0.0
    plt.close(fig)


def test_xtick_band_height_positive_for_category_labels():
    """Category labels below the axes register a positive measured band."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.bar(["forced", "calibrated", "recall-biased"], [0.6, 0.3, 0.8])
    fig.canvas.draw()
    band = _xtick_band_height_fig(fig, ax)
    assert band is not None and band > 0.0
    plt.close(fig)


def test_xtick_band_ignores_labels_above_axes():
    """Top-mounted x-ticks (bar_h / x_axis_top) don't count toward the band."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.barh(["a", "b", "c"], [1, 2, 3])
    ax.xaxis.tick_top()
    fig.canvas.draw()
    # Bottom band is empty (labels are on top) -> ~0.
    assert _xtick_band_height_fig(fig, ax) == 0.0
    plt.close(fig)


def test_category_chart_reserves_more_bottom_than_line_chart():
    """A categorical chart reserves at least as much bottom margin as a line
    chart with the same footnotes — the measured tick band is additive."""
    import numpy as np

    fig_bar, ax_bar = plt.subplots(figsize=(5.0, 3.4))
    ax_bar.bar(["forced", "calibrated", "recall-biased"], [0.6, 0.3, 0.8])
    finalize(ax_bar, title="T", descriptor="D", footnote_lines=2, source="S")
    bar_y0 = ax_bar.get_position().y0
    plt.close(fig_bar)

    fig_line, ax_line = plt.subplots(figsize=(5.0, 3.4))
    ax_line.plot(np.arange(5), [1, 3, 2, 5, 4])
    finalize(ax_line, title="T", descriptor="D", footnote_lines=2, source="S")
    line_y0 = ax_line.get_position().y0
    plt.close(fig_line)

    # Category labels are taller than single-row numeric ticks -> axes sits
    # at least as high (larger reserved bottom margin).
    assert bar_y0 >= line_y0 - 1e-3
