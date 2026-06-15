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


def test_finalize_has_no_auto_layout_param():
    """The auto_layout escape hatch is gone — passing it must error."""
    import inspect

    assert "auto_layout" not in inspect.signature(finalize).parameters
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    with pytest.raises(TypeError):
        finalize(ax, title="T", auto_layout=False)
    plt.close(fig)


def test_auto_layout_runs_unconditionally():
    """finalize always overwrites a caller's pre-set subplots_adjust margins.

    Previously ``auto_layout=False`` left the caller's margins untouched; now
    auto-layout always runs, so the pinned standard left margin wins over the
    bespoke one the caller set before ``finalize``.
    """
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    fig.subplots_adjust(left=0.40, right=0.55)  # deliberately odd pre-set
    finalize(ax, title="A title", descriptor="A descriptor", source="S")
    pos = ax.get_position()
    # finalize pins left=AUTO_LAYOUT_LEFT (0.02) / right=AUTO_LAYOUT_RIGHT (0.96).
    assert pos.x0 == pytest.approx(0.02, abs=1e-6)
    assert pos.x1 == pytest.approx(0.96, abs=1e-6)
    plt.close(fig)


def _title_top_y1(fig, fragment: str) -> float:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return max(
        t.get_window_extent(renderer=renderer).transformed(inv).y1
        for t in fig.texts
        if fragment in t.get_text()
    )


def test_faceted_override_after_finalize_restores_wspace_and_keeps_title():
    """The faceted pattern: finalize() then subplots_adjust(wspace=) after.

    The override must (a) widen the inter-panel gap and (b) leave the title
    attached just above the first panel — overriding wspace/left/right/bottom
    after finalize does not move the anchor panel's top-left corner.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.9))
    for ax in axes:
        ax.plot([0, 1, 2], [0, 1, 0])

    finalize(
        axes[0],
        title="A faceted chart title",
        descriptor="Across three panels",
        source="Source: test",
        title_x=0.04,
        y_start=0.075,
    )
    top_before = axes[0].get_position().y1
    gap_before = axes[1].get_position().x0 - axes[0].get_position().x1
    title_y1_before = _title_top_y1(fig, "faceted chart title")

    fig.subplots_adjust(wspace=0.35)
    gap_after = axes[1].get_position().x0 - axes[0].get_position().x1
    top_after = axes[0].get_position().y1
    title_y1_after = _title_top_y1(fig, "faceted chart title")

    # Inter-panel spacing widened.
    assert gap_after > gap_before
    # The anchor panel's top is unchanged, so the title stays attached.
    assert top_after == pytest.approx(top_before, abs=1e-9)
    assert title_y1_after == pytest.approx(title_y1_before, abs=1e-9)
    # Title sits within the figure, just above the first panel.
    assert title_y1_after <= 1.0
    plt.close(fig)
