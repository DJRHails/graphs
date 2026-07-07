"""y_axis_label vs the title stack: reserve a band, re-anchor, never overlap."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, y_axis_label

# The real failing case (touchstone figures/misclassification/
# length_control_guilt_vs_n.png): a long title, a wrapped descriptor, and a
# right-side y_axis_label(unit=...) rendered before finalize — the label was
# left stranded at the pre-layout axes top, overlapping the title.
TITLE = "Does stage-1 guilt track harm count when length is held constant?"
DESCRIPTOR = "Opus-4.8 label-free guilt call on the exact probed artifact"
LABEL = "mean measured guilt"
UNIT = "category-free guilt-o-meter, 0-100"


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _line_fig():
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.plot([1, 2, 4, 8], [20, 17, 59, 41], marker="o")
    ax.plot([1, 2, 4, 8], [35, 39, 72, 67], marker="o")
    ax.set_ylim(0, 100)
    return fig, ax


def _text_bboxes(fig):
    """(text, figure-coord bbox) for every non-empty fig.text artist."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    return [
        (t.get_text(), t.get_window_extent(renderer=renderer).transformed(inv))
        for t in fig.texts
        if t.get_text().strip()
    ]


def _split_label_vs_stack(fig):
    """Partition fig.texts into y_axis_label artists and title-stack artists."""
    label_bbs, stack_bbs = [], []
    for text, bb in _text_bboxes(fig):
        if text in (LABEL, UNIT):
            label_bbs.append((text, bb))
        else:
            stack_bbs.append((text, bb))
    return label_bbs, stack_bbs


def test_right_side_label_before_finalize_clears_title_stack():
    """The regression: label bboxes must not intersect any title-stack bbox."""
    fig, ax = _line_fig()
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR)

    label_bbs, stack_bbs = _split_label_vs_stack(fig)
    assert len(label_bbs) == 2  # text + unit line both rendered
    overlaps = [
        (lt, st) for lt, lbb in label_bbs for st, sbb in stack_bbs if lbb.overlaps(sbb)
    ]
    assert not overlaps, f"y_axis_label overlaps the title stack: {overlaps}"


def test_label_reanchors_between_descriptor_and_axes_top():
    """The block seats above the final axes top and below the descriptor."""
    fig, ax = _line_fig()
    y_axis_label(ax, LABEL, unit=UNIT)
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR)

    label_bbs, stack_bbs = _split_label_vs_stack(fig)
    axes_top = ax.get_position().y1
    desc_bb = next(bb for t, bb in stack_bbs if DESCRIPTOR.split()[0] in t)
    label_top = max(bb.y1 for _, bb in label_bbs)
    label_bottom = min(bb.y0 for _, bb in label_bbs)
    assert label_bottom >= axes_top - 1e-3, (
        f"label bottom {label_bottom:.4f} dips below the axes top {axes_top:.4f}"
    )
    assert label_top <= desc_bb.y0 + 1e-3, (
        f"label top {label_top:.4f} reaches into the descriptor (y0 {desc_bb.y0:.4f})"
    )


def test_left_side_label_clears_title_stack():
    """The dodge holds on a left-mounted label too (same side as the title)."""
    fig, ax = _line_fig()
    y_axis_label(ax, LABEL, unit=UNIT, side="left")
    finalize(ax, title=TITLE, descriptor=DESCRIPTOR, y_axis_right=False)

    label_bbs, stack_bbs = _split_label_vs_stack(fig)
    overlaps = [
        (lt, st) for lt, lbb in label_bbs for st, sbb in stack_bbs if lbb.overlaps(sbb)
    ]
    assert not overlaps, f"left-side y_axis_label overlaps the title stack: {overlaps}"


def test_label_band_drops_axes_below_no_label_layout():
    """The band is genuinely reserved: the axes top sits lower with a label."""
    fig_no, ax_no = _line_fig()
    finalize(ax_no, title=TITLE, descriptor=DESCRIPTOR)
    top_no = ax_no.get_position().y1

    fig_yes, ax_yes = _line_fig()
    y_axis_label(ax_yes, LABEL, unit=UNIT)
    finalize(ax_yes, title=TITLE, descriptor=DESCRIPTOR)
    top_yes = ax_yes.get_position().y1

    assert top_yes < top_no, (
        f"y_axis_label reserved no room (axes top {top_yes:.4f} vs {top_no:.4f})"
    )


def test_no_label_layout_unchanged():
    """No y_axis_label ⇒ no band: two identical charts lay out identically."""
    fig_a, ax_a = _line_fig()
    finalize(ax_a, title=TITLE, descriptor=DESCRIPTOR)
    top_a = ax_a.get_position().y1

    fig_b, ax_b = _line_fig()
    finalize(ax_b, title=TITLE, descriptor=DESCRIPTOR)
    top_b = ax_b.get_position().y1

    assert top_a == pytest.approx(top_b, abs=1e-9)


def test_label_after_finalize_stays_manual():
    """The documented manual path — label after finalize — is never moved."""
    fig, ax = _line_fig()
    finalize(ax, title="Short", descriptor="")
    y_axis_label(ax, LABEL)
    positions = [t.get_position() for t in fig.texts if t.get_text().strip() == LABEL]
    fig.canvas.draw()
    after = [t.get_position() for t in fig.texts if t.get_text().strip() == LABEL]
    assert positions == after
