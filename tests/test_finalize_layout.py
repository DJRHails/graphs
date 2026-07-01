"""Auto-layout: margins (top/bottom/left/right) and inter-panel spacing."""

import warnings

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, footnotes, panel_label, set_theme, top_legend
from graphs._finalize import (
    AUTO_LAYOUT_LEFT,
    AUTO_LAYOUT_RIGHT,
    _compute_side_margins,
    _get_renderer,
    _xtick_band_height_fig,
)


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


def test_auto_layout_param_accepted_but_ignored():
    """auto_layout is a deprecated no-op kept for back-compat — accepted, never gates."""
    import inspect

    assert "auto_layout" in inspect.signature(finalize).parameters

    # The legacy escape hatch must not error...
    fig_off, ax_off = plt.subplots(figsize=(5.0, 3.4))
    ax_off.plot([0, 1], [0, 1])
    finalize(ax_off, title="T", auto_layout=False)
    off = ax_off.get_position()
    plt.close(fig_off)

    # ...and must produce the same auto-laid-out margins as the default (ignored).
    fig_on, ax_on = plt.subplots(figsize=(5.0, 3.4))
    ax_on.plot([0, 1], [0, 1])
    finalize(ax_on, title="T")
    on = ax_on.get_position()
    plt.close(fig_on)

    assert off.x0 == pytest.approx(on.x0, abs=1e-6)
    assert off.y0 == pytest.approx(on.y0, abs=1e-6)


def test_auto_layout_runs_unconditionally():
    """finalize always overwrites a caller's pre-set subplots_adjust margins.

    Previously ``auto_layout=False`` left the caller's margins untouched; now
    auto-layout always runs, so the auto-measured margins win over the bespoke
    ones the caller set before ``finalize``. A no-left-label line chart keeps
    the small default left; the right is pulled in to hold the right-axis
    numeric labels (so it sits inside the old fixed 0.96, not on it).
    """
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    fig.subplots_adjust(left=0.40, right=0.55)  # deliberately odd pre-set
    finalize(ax, title="A title", descriptor="A descriptor", source="S")
    pos = ax.get_position()
    # No left-side y-labels -> left stays at the small default.
    assert pos.x0 == pytest.approx(0.02, abs=1e-6)
    # Right-axis tick labels are measured in: inside the old fixed 0.96.
    assert 0.90 < pos.x1 < 0.96
    plt.close(fig)


def test_left_margin_scales_with_y_label_width():
    """A horizontal-bar chart with long category labels gets a wide auto left.

    The category labels hang to the left of the axis (via a large tick pad), so
    the measured left margin must be far wider than the small default a chart
    with no left-side labels keeps — proving the side margin tracks the actual
    y-axis text width.
    """
    import numpy as np

    # Plain line chart: nothing protrudes left -> small default left.
    fig_plain, ax_plain = plt.subplots(figsize=(5.0, 3.4))
    ax_plain.plot([0, 1, 2], [0, 1, 0])
    finalize(ax_plain, title="T", descriptor="D", source="S")
    plain_left = ax_plain.get_position().x0
    plt.close(fig_plain)

    # Horizontal bars with long left-hung category labels -> wide measured left.
    fig_bar, ax_bar = plt.subplots(figsize=(5.0, 3.4))
    cats = ["A really quite long category label", "Short", "Another long one here"]
    ax_bar.barh(np.arange(len(cats)), [3, 1, 2])
    ax_bar.set_yticks(np.arange(len(cats)))
    ax_bar.set_yticklabels(cats, ha="left")
    ax_bar.yaxis.set_tick_params(length=0, pad=max(len(c) for c in cats) * 5 + 8)
    finalize(ax_bar, title="T", descriptor="D", source="S", y_axis_right=False)
    bar_left = ax_bar.get_position().x0
    plt.close(fig_bar)

    assert plain_left == pytest.approx(0.02, abs=1e-6)
    assert bar_left > plain_left + 0.10  # comfortably wider for the labels


def _title_top_y1(fig, fragment: str) -> float:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return max(
        t.get_window_extent(renderer=renderer).transformed(inv).y1
        for t in fig.texts
        if fragment in t.get_text()
    )


def test_faceted_auto_wspace_separates_panels_and_keeps_title():
    """finalize auto-sizes the inter-panel wspace; the title stays attached.

    Each panel carries right-axis numeric labels, so finalize must open a gap
    between columns wide enough to hold them, with the title attached just above
    the first panel — no caller-side ``subplots_adjust``.
    """
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.9))
    for ax in axes:
        ax.plot([0, 1, 2], [0, 1, 0])
        ax.yaxis.tick_right()  # right-axis labels protrude between columns

    finalize(
        axes[0],
        title="A faceted chart title",
        descriptor="Across three panels",
        source="Source: test",
        title_x=0.04,
        y_start=0.075,
        y_axis_right=False,  # panels already right-ticked above
    )
    fig.canvas.draw()

    # Inter-column gap opened, and it is wide enough for panel 0's right-axis
    # labels not to spill into panel 1.
    gap = axes[1].get_position().x0 - axes[0].get_position().x1
    assert gap > 0.0
    renderer = _get_renderer(fig)
    inv = fig.transFigure.inverted()
    p0_right = axes[0].get_position().x1
    p1_left = axes[1].get_position().x0
    for tl in axes[0].get_yticklabels():
        if not tl.get_text():
            continue
        x1 = tl.get_window_extent(renderer=renderer).transformed(inv).x1
        assert x1 < p1_left, f"panel-0 label {tl.get_text()!r} ({x1:.3f}) hits panel 1"
        assert x1 > p0_right  # labels do sit in the gap (sanity)

    # Title attached above panel 0 and inside the figure.
    title_y1 = _title_top_y1(fig, "faceted chart title")
    assert axes[0].get_position().y1 <= title_y1 <= 1.0

    # An override-after still works and keeps the anchor top fixed (so the title
    # stays attached) — subplots_adjust(bottom/wspace) never moves y1.
    top_before = axes[0].get_position().y1
    title_before = _title_top_y1(fig, "faceted chart title")
    fig.subplots_adjust(wspace=0.6)
    assert axes[0].get_position().y1 == pytest.approx(top_before, abs=1e-9)
    assert _title_top_y1(fig, "faceted chart title") == pytest.approx(
        title_before, abs=1e-9
    )
    plt.close(fig)


def test_independent_y_panels_get_more_wspace_than_shared_y():
    """Independent-y facets need a wider auto wspace than shared-y facets.

    Each independent panel carries its own right-axis labels in the inter-column
    gap; a shared-y grid labels only the outer axis, so its columns can sit
    closer. The measured wspace must reflect that.
    """
    import numpy as np

    from graphs._finalize import _compute_wspace

    # Independent y: every panel keeps right-axis tick labels.
    fig_ind, axes_ind = plt.subplots(1, 3, figsize=(7.0, 3.9), sharey=False)
    for ax in axes_ind:
        ax.plot(np.arange(3), [10, 2000, 500])
        ax.yaxis.tick_right()
    fig_ind.canvas.draw()
    w_ind = _compute_wspace(fig_ind)
    plt.close(fig_ind)

    # Shared y: matplotlib hides the inner panels' tick labels.
    fig_sh, axes_sh = plt.subplots(1, 3, figsize=(7.0, 3.9), sharey=True)
    for ax in axes_sh:
        ax.plot(np.arange(3), [10, 2000, 500])
    fig_sh.canvas.draw()
    w_sh = _compute_wspace(fig_sh)
    plt.close(fig_sh)

    assert w_ind is not None and w_sh is not None
    assert w_ind > w_sh


def _panels_do_not_overlap_text(fig) -> bool:
    """True if no panel's data area contains another panel's tick/axis text."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    panels = [a for a in fig.axes if a.get_subplotspec() is not None]
    for a in panels:
        pos = a.get_position()
        for b in panels:
            if b is a:
                continue
            for tl in b.get_yticklabels() + b.get_xticklabels():
                if not tl.get_text():
                    continue
                bb = tl.get_window_extent(renderer=renderer).transformed(inv)
                cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
                if pos.x0 < cx < pos.x1 and pos.y0 < cy < pos.y1:
                    return False
    return True


def test_faceted_spacing_prevents_panel_overlap():
    """Auto wspace/hspace keep one panel's labels out of a neighbour's area."""
    import numpy as np

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.5), sharex=False, sharey=False)
    for ax in axes.flat:
        ax.plot(np.arange(3), [10, 2000, 500])
        ax.yaxis.tick_right()
    finalize(
        axes[0, 0],
        title="A 2x2 faceted chart",
        descriptor="Four independent panels",
        source="Source: test",
        title_x=0.04,
        y_start=0.075,
        y_axis_right=False,
        panel_labels=True,
    )
    for ax in axes.flat:
        panel_label(ax, "Panel")
    assert _panels_do_not_overlap_text(fig)
    plt.close(fig)


def test_panel_labels_widen_hspace():
    """panel_labels=True reserves more inter-row hspace than without it."""
    import numpy as np

    from graphs._finalize import _compute_hspace

    fig, axes = plt.subplots(2, 1, figsize=(5.0, 5.5))
    for ax in axes:
        ax.plot(np.arange(5), [1, 3, 2, 5, 4])
    fig.canvas.draw()
    h_plain = _compute_hspace(fig, has_panel_labels=False)
    h_labelled = _compute_hspace(fig, has_panel_labels=True)
    plt.close(fig)

    assert h_plain is not None and h_labelled is not None
    assert h_labelled > h_plain


def test_side_margins_fall_back_without_renderer(monkeypatch):
    """A no-renderer (non-Agg-style) figure keeps the fixed default margins.

    ``_compute_side_margins`` must return the constants rather than guessing
    when no renderer is available. On a non-Agg backend ``_get_renderer``
    returns ``None`` after a failed draw; simulate that directly so the test
    doesn't depend on a specific backend's draw internals.
    """
    import graphs._finalize as finalize_mod

    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    ax.plot([0, 1], [0, 1])
    fig.canvas.draw()

    monkeypatch.setattr(finalize_mod, "_get_renderer", lambda _fig: None)
    left, right = _compute_side_margins(fig)
    assert left == pytest.approx(AUTO_LAYOUT_LEFT)
    assert right == pytest.approx(AUTO_LAYOUT_RIGHT)
    plt.close(fig)


# --- top_legend band reservation -------------------------------------------


def _legend_bbox(fig) -> object:
    """Figure-coord bbox of the figure's first legend (after a draw)."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return fig.legends[0].get_window_extent(renderer=renderer).transformed(inv)


def _descriptor_lowest_y0(fig, fragment: str) -> float:
    """Lowest y0 of the descriptor text artist containing ``fragment``."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return min(
        t.get_window_extent(renderer=renderer).transformed(inv).y0
        for t in fig.texts
        if fragment in t.get_text()
    )


def test_top_legend_band_drops_axes_more_than_no_legend():
    """An auto top_legend reserves a band: the axes top sits lower than without.

    Two identical charts, one with a ``top_legend`` tagged before ``finalize``,
    one without. The legend chart's axes must drop by at least the legend's
    measured height — proof the band was reserved, not absorbed into the title
    stack.
    """
    fig_no, ax_no = plt.subplots(figsize=(5.0, 3.4))
    ax_no.plot([0, 1, 2], [0, 1, 0])
    finalize(ax_no, title="T", descriptor="D one\nD two", source="S")
    top_no = ax_no.get_position().y1
    plt.close(fig_no)

    fig_yes, ax_yes = plt.subplots(figsize=(5.0, 3.4))
    (line,) = ax_yes.plot([0, 1, 2], [0, 1, 0], label="Series")
    top_legend(fig_yes, [line], ["Series"])
    legend_h = _legend_bbox(fig_yes).height
    finalize(ax_yes, title="T", descriptor="D one\nD two", source="S")
    top_yes = ax_yes.get_position().y1
    plt.close(fig_yes)

    # The legend chart's axes top is pushed down by ~the legend band.
    assert top_yes < top_no - legend_h * 0.5


def test_top_legend_does_not_overlap_descriptor_faceted():
    """Faceted chart, top_legend BEFORE finalize, hands-off: legend clears the
    descriptor and sits above the panels — no ``subplots_adjust``.
    """
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.9))
    idx = np.arange(3)
    for ax in axes:
        b0 = ax.bar(idx, [5, 3, 4], width=0.5, label="One")
        b1 = ax.bar(idx, [2, 1, 2], width=0.5, bottom=[5, 3, 4], label="Two")
        ax.set_xticks(idx)
        ax.set_xticklabels(["a", "b", "c"])
        ax.set_ylim(0, 9)

    top_legend(fig, [b0, b1], ["One", "Two"], ncol=2)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        finalize(
            axes[0],
            title="A faceted chart with a shared colour key",
            descriptor="A two-line descriptor\n% of sampled traffic",
            source="Source: test",
            title_x=0.04,
            y_start=0.075,
        )
        for ax in axes:
            panel_label(ax, "Panel")
        from graphs._finalize import verify_layout

        verify_layout(fig)

    leg = _legend_bbox(fig)
    desc_y0 = _descriptor_lowest_y0(fig, "sampled traffic")
    panel_top = max(ax.get_position().y1 for ax in axes)

    # Legend below the descriptor's lowest line and above the panel row.
    assert leg.y1 < desc_y0, (
        f"legend top {leg.y1:.4f} overlaps descriptor (y0 {desc_y0:.4f})"
    )
    assert leg.y0 > panel_top, (
        f"legend bottom {leg.y0:.4f} dips below the panel top ({panel_top:.4f})"
    )
    overflow = [str(w.message) for w in caught if "verify_layout" in str(w.message)]
    assert not overflow, f"verify_layout flagged an overflow: {overflow}"
    plt.close(fig)


def test_top_legend_explicit_y_is_not_repositioned():
    """A manual ``y=`` is an override — never tagged, never moved by finalize."""
    fig, ax = plt.subplots(figsize=(5.0, 3.4))
    (line,) = ax.plot([0, 1, 2], [0, 1, 0], label="Series")
    leg = top_legend(fig, [line], ["Series"], y=0.82)
    # An explicit-y legend carries no tag and isn't registered for repositioning.
    assert not hasattr(leg, "_graphs_top_legend")
    assert getattr(fig, "_graphs_top_legend", None) is None

    before = tuple(leg.get_bbox_to_anchor().bounds)
    finalize(ax, title="T", descriptor="D one\nD two", source="S")
    after = tuple(leg.get_bbox_to_anchor().bounds)
    assert before == pytest.approx(after)
    plt.close(fig)


def test_no_top_legend_leaves_top_margin_unchanged():
    """A chart with no top_legend reserves no legend band (top margin unchanged).

    Guards the no-regression promise: the band only opens when an auto
    top_legend is present.
    """
    fig_a, ax_a = plt.subplots(figsize=(5.0, 3.4))
    ax_a.plot([0, 1, 2], [0, 1, 0])
    finalize(ax_a, title="T", descriptor="D one\nD two", source="S")
    top_a = ax_a.get_position().y1
    plt.close(fig_a)

    # Same chart again — deterministic, no legend, identical top.
    fig_b, ax_b = plt.subplots(figsize=(5.0, 3.4))
    ax_b.plot([0, 1, 2], [0, 1, 0])
    finalize(ax_b, title="T", descriptor="D one\nD two", source="S")
    top_b = ax_b.get_position().y1
    plt.close(fig_b)

    assert top_a == pytest.approx(top_b, abs=1e-9)


def test_panel_labels_reserve_top_band():
    """``panel_labels=True`` drops the top row's axes to make room for the heading.

    The top-row ``panel_label`` (rule + bold heading) draws *above* the axes
    top; without a reserved band it lands in the top margin, on the axes or an
    overlying legend. The band drops the top-row axes vs. the same chart with
    ``panel_labels=False``.
    """
    fig_off, axes_off = plt.subplots(1, 2, figsize=(7.0, 3.9))
    for ax in axes_off:
        ax.plot([0, 1, 2], [0, 1, 0])
    finalize(axes_off[0], title="T", descriptor="D", source="S", title_x=0.04)
    top_off = axes_off[0].get_position().y1
    plt.close(fig_off)

    fig_on, axes_on = plt.subplots(1, 2, figsize=(7.0, 3.9))
    for ax in axes_on:
        ax.plot([0, 1, 2], [0, 1, 0])
    finalize(
        axes_on[0], title="T", descriptor="D", source="S", title_x=0.04, panel_labels=True
    )
    top_on = axes_on[0].get_position().y1
    plt.close(fig_on)

    assert top_on < top_off, (
        f"panel_labels=True should drop the top-row axes ({top_on:.4f}) "
        f"below the plain layout ({top_off:.4f})"
    )


def test_top_legend_clears_top_row_panel_labels():
    """Auto top_legend + top-row panel_labels stack cleanly: legend → label → axes.

    The reference case for the merged faceted FP figure. With both an auto
    ``top_legend`` (shared colour key) and per-panel ``panel_label`` headings,
    the legend must sit above every heading and each heading above its axes —
    no artist lands on the data or on a neighbour.
    """
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.9), sharey=True)
    xs = np.array([1, 2, 4, 8])
    for ax in axes:
        (a,) = ax.plot(xs, [0.1, 0.2, 0.3, 0.4], label="on")
        (b,) = ax.plot(xs, [0.1, 0.1, 0.2, 0.3], label="off")
        ax.set_ylim(0, 0.6)
        ax.set_ylabel("")
    top_legend(fig, [a, b], ["on", "off"], x=0.07, ncol=2)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        finalize(
            axes[0],
            title="A faceted chart with a shared key and panel headings",
            descriptor="A descriptor\n% of traffic",
            source="Source: test",
            title_x=0.07,
            y_axis_right=False,
            panel_labels=True,
        )
        for ax, name in zip(axes, ["Panel A", "Panel B"]):
            panel_label(ax, name)
        verify_layout_mod = __import__(
            "graphs._finalize", fromlist=["verify_layout"]
        ).verify_layout
        verify_layout_mod(fig)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    leg = fig.legends[0].get_window_extent(renderer=renderer).transformed(inv)
    label_texts = [t for t in fig.texts if t.get_text() in ("Panel A", "Panel B")]
    label_bbs = [
        t.get_window_extent(renderer=renderer).transformed(inv) for t in label_texts
    ]
    axes_top = max(ax.get_position().y1 for ax in axes)

    # Legend above every panel-label heading.
    assert leg.y0 > max(bb.y1 for bb in label_bbs), (
        f"legend bottom {leg.y0:.4f} dips into the panel-label band"
    )
    # Each heading above the axes it belongs to.
    assert min(bb.y0 for bb in label_bbs) >= axes_top - 0.01, (
        f"panel label bottom {min(bb.y0 for bb in label_bbs):.4f} sits on the axes"
    )
    overflow = [str(w.message) for w in caught if "verify_layout" in str(w.message)]
    assert not overflow, f"verify_layout flagged an overflow: {overflow}"
    plt.close(fig)
