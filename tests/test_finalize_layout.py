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


def _stacked_rows(fig, *, below: float = 0.30):
    """Bottom-band text rows as ``(y0, y1, text)``, ordered bottom-to-top."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    rows = []
    for t in fig.texts:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer=renderer).transformed(inv)
        if bb.y1 < below:
            rows.append((bb.y0, bb.y1, t.get_text()))
    return sorted(rows)


def test_stacked_footnotes_one_row_per_note():
    """``footnotes(stack=True)`` renders each note on its own line plus a source row.

    Three short definitions plus a source line must land as four distinct,
    non-overlapping rows in the bottom band — the case the touchstone
    ``_stacked_mode_footnote`` workaround hand-rolled. Bottom-to-top the source
    is lowest and each note sits one line box above the previous, so no two
    rows share a baseline.
    """
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([1, 2, 3], [0, 1, 2])
    ax.set_xlim(0.5, 3.5)
    ax.set_xticks([1, 2, 3])
    ax.set_xlabel("an x-axis label the footnote stack must clear")
    notes = ("alpha: first definition", "beta: second definition", "gamma: third definition")
    finalize(ax, title="T", descriptor="D", source="", footnote_lines=len(notes) + 1)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, *notes, source="Source: test", stack=True, check_anchors=False)

    rows = _stacked_rows(fig)
    assert len(rows) == len(notes) + 1, (
        f"expected {len(notes) + 1} stacked rows, got {len(rows)}: {[r[2] for r in rows]}"
    )
    # The lowest row is the source; every other row is a distinct note.
    assert rows[0][2].startswith("Source"), f"bottom row should be the source, got {rows[0][2]!r}"
    # Each row sits strictly above the one below it (no shared baseline / overlap).
    for lower, upper in zip(rows, rows[1:]):
        assert upper[0] >= lower[1] - 1e-3, (
            f"row {upper[2]!r} (y0={upper[0]:.4f}) overlaps row {lower[2]!r} (y1={lower[1]:.4f})"
        )
    overflow = [str(w.message) for w in caught if "verify_layout" in str(w.message)]
    assert not overflow, f"verify_layout flagged an overflow: {overflow}"
    plt.close(fig)


def test_stacked_footnotes_clear_the_xlabel():
    """The stacked block sits entirely below the x-axis label — no collision.

    ``footnotes(stack=True)`` anchors its bottom-most row below the lowest
    x-tick label / xlabel; every stacked row (including the top-most note) must
    stay under the xlabel's bottom edge so the definitions never overwrite it.
    """
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([1, 2, 3], [0, 1, 2])
    ax.set_xlim(0.5, 3.5)
    ax.set_xticks([1, 2, 3])
    ax.set_xlabel("an x-axis label the footnote stack must clear")
    notes = ("alpha: first", "beta: second", "gamma: third")
    finalize(ax, title="T", descriptor="D", source="", footnote_lines=len(notes) + 1)
    footnotes(fig, *notes, source="Source: test", stack=True, check_anchors=False)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    xlabel_y0 = ax.xaxis.label.get_window_extent(renderer=renderer).transformed(inv).y0
    rows = _stacked_rows(fig)
    highest_row_top = max(r[1] for r in rows)
    assert highest_row_top <= xlabel_y0 + 1e-3, (
        f"top stacked row (y1={highest_row_top:.4f}) collides with the xlabel "
        f"(y0={xlabel_y0:.4f})"
    )
    plt.close(fig)


def _bottom_row_geometry(fig):
    """Bottom-band rows as ``(y0, x0, text)`` rounded for cross-figure comparison."""
    return [(round(y0, 4), round(x0, 4), text) for y0, _, text, x0 in _stacked_rows_x(fig)]


def _stacked_rows_x(fig, *, below: float = 0.30):
    """Like :func:`_stacked_rows` but carrying each row's left edge too."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    rows = []
    for t in fig.texts:
        if not t.get_text().strip():
            continue
        bb = t.get_window_extent(renderer=renderer).transformed(inv)
        if bb.y1 < below:
            rows.append((bb.y0, bb.y1, t.get_text(), bb.x0))
    return sorted(rows)


def _footnoted_fig(*notes, source="Source: test", **footnote_kwargs):
    """A single-panel chart with ``footnotes(*notes, source=...)`` applied."""
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([1, 2, 3], [0, 1, 2])
    ax.set_xticks([1, 2, 3])
    finalize(ax, title="T", descriptor="D", source="")
    footnotes(fig, *notes, source=source, check_anchors=False, **footnote_kwargs)
    return fig


def test_auto_stack_multi_note_matches_explicit_stack():
    """``stack`` unset with two notes renders the stacked layout, not the packed row.

    The auto default must be indistinguishable from ``stack=True`` — same rows
    at the same positions — and must NOT reproduce the packed layout.
    """
    notes = ("*first definition", "†second definition")
    auto = _bottom_row_geometry(_footnoted_fig(*notes))
    forced = _bottom_row_geometry(_footnoted_fig(*notes, stack=True))
    packed = _bottom_row_geometry(_footnoted_fig(*notes, stack=False))
    assert auto == forced, f"auto != stack=True:\n{auto}\nvs\n{forced}"
    assert auto != packed, "auto default reproduced the packed layout for two notes"
    plt.close("all")


def test_auto_stack_single_short_note_stays_packed():
    """A single note that fits on the source row keeps the packed one-row layout.

    The Economist age-gap pattern — note right-aligned on the source row — is
    the one case pack mode earns; the auto default must leave it byte-similar
    to ``stack=False``.
    """
    note = "*short note"
    auto = _bottom_row_geometry(_footnoted_fig(note))
    packed = _bottom_row_geometry(_footnoted_fig(note, stack=False))
    forced = _bottom_row_geometry(_footnoted_fig(note, stack=True))
    assert auto == packed, f"auto != stack=False:\n{auto}\nvs\n{packed}"
    assert auto != forced, "a single short note should not auto-stack"
    # Packed means one shared row: note and source at the same baseline band.
    (src_y0, _, _), (note_y0, _, _) = sorted(auto)[:2]
    assert abs(src_y0 - note_y0) < 5e-3, f"note not packed on the source row: {auto}"
    plt.close("all")


def test_auto_stack_single_wrapping_note_stacks():
    """A single note too long for one row auto-picks the stacked layout."""
    note = (
        "*a very long definition that cannot possibly fit on a single footnote row "
        "because it keeps going and going, spelling out the whole condition with an "
        "example where one helps, e.g. 0-10 means eleven levels and 1-5 means five"
    )
    auto = _bottom_row_geometry(_footnoted_fig(note))
    forced = _bottom_row_geometry(_footnoted_fig(note, stack=True))
    assert auto == forced, f"auto != stack=True:\n{auto}\nvs\n{forced}"
    plt.close("all")


def test_stacked_wrapped_notes_grow_bottom_band():
    """Long stacked notes never overflow — no ``footnote_lines``, no ``stack`` needed.

    The regression: three ~180-char notes wrap to ~2 rows each, but the band
    reservation counted one row per note, pushing the source line off the
    bottom edge. ``footnotes()`` must measure the wrapped rows itself and grow
    the bottom margin, with the caller passing nothing.
    """
    from graphs import subplots

    long_notes = tuple(
        f"{marker}{body}"
        for marker, body in [
            ("*", "first regime: the monitor answers the harm question on every "
                  "transcript with no abstain option, so borderline benign "
                  "transcripts get pushed over the flagging threshold anyway"),
            ("†", "second regime: the monitor emits a calibrated probability and "
                  "a deployment-tuned threshold converts it into a flag, which "
                  "absorbs most of the borderline mass before human review"),
            ("‡", "third category: transcripts whose surface features match a "
                  "harm taxonomy entry but whose full context shows no policy "
                  "violation on a careful reading of the whole exchange"),
        ]
    )
    fig, axes = subplots("wide", height=4.0, ncols=2, sharey=True)
    for ax in axes:
        ax.bar([0, 1], [3, 5], 0.6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Forced", "Calibrated"])
    finalize(axes[0], title="T", descriptor="D", source="")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, *long_notes, source="Source: test", check_anchors=False)
    overflow = [str(w.message) for w in caught if "verify_layout" in str(w.message)]
    assert not overflow, f"stacked notes overflowed the bottom band: {overflow}"
    # The block really is stacked: three notes + source, one text block per row.
    rows = _stacked_rows(fig)
    assert rows[0][2].startswith("Source"), f"bottom row should be the source: {rows}"
    plt.close(fig)


def _legacy_footnoted_fig(*notes, **footnote_kwargs):
    """A single-panel chart with no-source (legacy-anchor) ``footnotes`` applied."""
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([1, 2, 3], [0, 1, 2])
    ax.set_xticks([1, 2, 3])
    finalize(ax, title="T", descriptor="D", source="Source: test")
    footnotes(fig, *notes, check_anchors=False, **footnote_kwargs)
    return fig


def test_auto_stack_no_source_single_short_note_stays_packed():
    """With no ``source``, a single one-line note keeps the legacy anchor.

    ``_auto_stack``'s source-less branch: a note that fits one row must
    resolve packed (byte-similar to ``stack=False``), not stacked — the
    discriminating case a regression to "always stack" would break.
    """
    note = "*short note"
    auto = _bottom_row_geometry(_legacy_footnoted_fig(note))
    packed = _bottom_row_geometry(_legacy_footnoted_fig(note, stack=False))
    forced = _bottom_row_geometry(_legacy_footnoted_fig(note, stack=True))
    assert auto == packed, f"auto != stack=False:\n{auto}\nvs\n{packed}"
    assert auto != forced, "a single short no-source note should not auto-stack"
    plt.close("all")


def test_auto_stack_wrap_false_stays_packed():
    """``stack=None`` + ``wrap=False`` resolves packed even for a wrapping-length note.

    With wrapping disabled the packed path renders one (overflowing) row, so
    the auto default must not silently switch layouts on the caller.
    """
    note = (
        "*a very long definition that would certainly word-wrap on a single "
        "footnote row if wrapping were enabled, spelling the condition out in full"
    )
    # verify=False: the un-wrapped row overflowing the right edge is the
    # scenario itself, not a layout bug this test should warn about.
    auto = _bottom_row_geometry(_legacy_footnoted_fig(note, wrap=False, verify=False))
    packed = _bottom_row_geometry(
        _legacy_footnoted_fig(note, wrap=False, stack=False, verify=False)
    )
    assert auto == packed, f"auto != stack=False:\n{auto}\nvs\n{packed}"
    plt.close("all")


def test_stacked_explicit_y_skips_band_growth():
    """An explicit ``y`` pins placement: the stacked path must not grow the margin."""
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([1, 2, 3], [0, 1, 2])
    ax.set_xticks([1, 2, 3])
    finalize(ax, title="T", descriptor="D", source="")
    bottom_before = fig.subplotpars.bottom
    notes = ("*first definition", "†second definition", "‡third definition")
    footnotes(
        fig, *notes, source="Source: test", stack=True, y=0.12,
        check_anchors=False, verify=False,
    )
    assert fig.subplotpars.bottom == pytest.approx(bottom_before), (
        "explicit y must leave the bottom margin untouched "
        f"(before={bottom_before:.4f}, after={fig.subplotpars.bottom:.4f})"
    )
    plt.close(fig)


def test_multirow_grid_stacked_overflow_names_footnote_lines():
    """On a multi-row grid the stack can't grow the margin — the warning must say so.

    ``_ensure_bottom_clearance`` deliberately no-ops on ``nrows > 1``; when the
    reserved band is too shallow the failure surfaces as warnings, and at least
    one must name the actual remedy: ``finalize(footnote_lines=<rows>)``.
    """
    from graphs import subplots

    long_notes = tuple(
        f"{marker}a long definition that wraps to several continuation rows on "
        "this figure width because it keeps going and going with the full "
        "spelled-out condition and an example where one helps the reader"
        for marker in ("*", "†", "‡")
    )
    fig, axes = subplots("wide", height=4.5, nrows=2)
    for ax in axes:
        ax.plot([1, 2, 3], [0, 1, 2])
        ax.set_xticks([1, 2, 3])
    finalize(axes[0], title="T", descriptor="D", source="", panel_labels=True)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        footnotes(fig, *long_notes, source="Source: test", check_anchors=False)
    hints = [str(w.message) for w in caught if "footnote_lines=" in str(w.message)]
    assert hints, (
        "expected a warning naming finalize(footnote_lines=...) on a multi-row "
        f"grid whose stacked notes overflow; got: {[str(w.message) for w in caught]}"
    )
    plt.close(fig)


# --- legend-band vs footnotes call order (issue #15) --------------------------


def _shrink_axes_for_legend_band(fig, ax, *, ncol: int | None = None):
    """Downstream legend-band pattern (touchstone ``lab.utils.plotting.legend_band``).

    Shrinks the axes top with ``ax.set_position`` to free a band between the
    descriptor and the data, then anchors an explicit-``y`` :func:`top_legend`
    at the *pre-shrink* axes top so the legend fills the freed band instead of
    drawing over the data. ``finalize`` never re-anchors an explicit-``y``
    legend, so the layout only holds if nothing snaps the axes back to its
    gridspec position afterwards.
    """
    import math

    handles, labels = ax.get_legend_handles_labels()
    if ncol is None:
        ncol = max(1, len(handles))
    n_rows = math.ceil(len(handles) / ncol)
    fig.canvas.draw()
    pos = ax.get_position()
    ax.set_position((pos.x0, pos.y0, pos.width, pos.height - 0.05 * n_rows))
    return top_legend(fig, handles, labels, y=pos.y1, ncol=ncol)


def _line_chart_with_series(figsize=(6.4, 4.6)):
    """A line chart whose top series reaches the top of the y-range."""
    fig, ax = plt.subplots(figsize=figsize)
    for i in range(3):
        ax.plot([0, 1, 2], [i, i + 1, i + 2], label=f"series {i}")
    ax.set_ylim(0, 4)  # the top line touches y=4: any legend over the axes hits it
    ax.set_xticks([0, 1, 2])
    return fig, ax


@pytest.mark.parametrize(
    "notes",
    [
        pytest.param(
            (
                "*first definition on its own stacked row",
                "†second definition on its own stacked row",
            ),
            id="stacked-band",
        ),
        pytest.param(("*short note",), id="packed-band"),
    ],
)
def test_legend_band_before_footnotes_keeps_legend_above_axes(notes):
    """legend-band first, footnotes second: the freed band must survive.

    The v0.9.0 regression: ``footnotes``'s self-sizing bottom band grew the
    margin through ``subplots_adjust``, which re-derives every axes position
    from the gridspec — wiping the manual axes shrink and leaving the
    explicit-``y`` legend hanging over the restored axes top (the
    legend-over-line mis-render). Both footnote layouts (stacked and packed)
    grow the band, so both must preserve the shrink.
    """
    fig, ax = _line_chart_with_series()
    finalize(ax, title="T", descriptor="D", source="")
    top_before_band = ax.get_position().y1

    _shrink_axes_for_legend_band(fig, ax)
    shrunk_top = ax.get_position().y1
    assert shrunk_top < top_before_band - 0.01  # sanity: a band was freed

    footnotes(fig, *notes, source="Source: test", check_anchors=False)

    grown_y0 = ax.get_position().y0
    assert ax.get_position().y1 == pytest.approx(shrunk_top, abs=1e-6), (
        f"footnotes reset the axes top to {ax.get_position().y1:.4f}, undoing the "
        f"legend-band shrink (expected {shrunk_top:.4f})"
    )
    leg = _legend_bbox(fig)
    # The legend box grazes the axes top by ~1pt even in the documented
    # footnotes-first order (the downstream 0.05-per-row band vs matplotlib's
    # borderaxespad slack); the regression overlapped by the FULL 0.05 shrink.
    assert leg.y0 >= ax.get_position().y1 - 0.005, (
        f"legend bottom {leg.y0:.4f} overlaps the axes (top {ax.get_position().y1:.4f}) "
        "— the legend is drawn over the data lines"
    )
    # The bottom band still did its job: footnote rows sit below the x-tick labels.
    assert _bottom_band_top(fig) < _xtick_band_y0(fig, ax)
    assert grown_y0 > 0.0
    plt.close(fig)


def test_legend_band_and_footnotes_order_independent():
    """footnotes-then-legend-band and legend-band-then-footnotes match exactly.

    Downstream (touchstone) hand-ordered 35 call sites footnotes-first to dodge
    the reset; either order must now produce the same axes geometry, the same
    legend box, and the same footnote rows.
    """
    notes = (
        "*first definition on its own stacked row",
        "†second definition on its own stacked row",
    )

    fig_doc, ax_doc = _line_chart_with_series()
    finalize(ax_doc, title="T", descriptor="D", source="")
    footnotes(fig_doc, *notes, source="Source: test", check_anchors=False)
    _shrink_axes_for_legend_band(fig_doc, ax_doc)
    pos_doc = ax_doc.get_position()
    leg_doc = _legend_bbox(fig_doc)
    rows_doc = _bottom_row_geometry(fig_doc)
    plt.close(fig_doc)

    fig_rev, ax_rev = _line_chart_with_series()
    finalize(ax_rev, title="T", descriptor="D", source="")
    _shrink_axes_for_legend_band(fig_rev, ax_rev)
    footnotes(fig_rev, *notes, source="Source: test", check_anchors=False)
    pos_rev = ax_rev.get_position()
    leg_rev = _legend_bbox(fig_rev)
    rows_rev = _bottom_row_geometry(fig_rev)
    plt.close(fig_rev)

    assert pos_rev.bounds == pytest.approx(pos_doc.bounds, abs=1e-4), (
        f"axes geometry depends on call order: {pos_rev.bounds} vs {pos_doc.bounds}"
    )
    assert (leg_rev.x0, leg_rev.y0, leg_rev.x1, leg_rev.y1) == pytest.approx(
        (leg_doc.x0, leg_doc.y0, leg_doc.x1, leg_doc.y1), abs=1e-4
    ), "legend box depends on call order"
    assert rows_rev == rows_doc, (
        f"footnote rows depend on call order:\n{rows_rev}\nvs\n{rows_doc}"
    )


def test_bottom_clearance_growth_matches_subplots_adjust_when_untouched():
    """No manual repositioning: the in-place growth equals the old gridspec path.

    Guards the no-regression promise — a figure whose axes were only ever
    placed by ``finalize`` must land exactly where ``subplots_adjust`` used to
    put it, and the recorded ``subplotpars.bottom`` must stay in sync so a
    caller's own ``subplots_adjust`` override after ``footnotes`` still starts
    from the grown margin.
    """
    notes = ("*first definition row", "†second definition row")
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot([0, 1, 2], [0, 1, 2])
    ax.set_xticks([0, 1, 2])
    finalize(ax, title="T", descriptor="D", source="")
    footnotes(fig, *notes, source="Source: test", check_anchors=False)

    pos = ax.get_position()
    assert fig.subplotpars.bottom == pytest.approx(pos.y0, abs=1e-9)
    # A caller override that only touches wspace must not move the grown bottom.
    fig.subplots_adjust(wspace=0.5)
    assert ax.get_position().y0 == pytest.approx(pos.y0, abs=1e-9)
    plt.close(fig)
