"""y_axis_label clears in-axes annotations that poke above the axes top."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, subplots, y_axis_label


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _label_bottom_and_annotation_top(fanned: bool) -> tuple[float, float]:
    fig, ax = subplots("wide", height=4.0)
    xs = [0.2, 0.4, 0.6, 0.64]
    ys = [0.995, 0.997, 0.999, 0.998]
    ax.plot(xs, ys, "o")
    if fanned:
        # The hatch-variants shape: labels fanned upward from points pinned
        # near the top edge, poking above the axes.
        for x, y, lane in zip(xs, ys, [(8, 10), (8, -16), (8, 30), (8, -36)], strict=True):
            ax.annotate("arm-label", (x, y), textcoords="offset points", xytext=lane, fontsize=8)
    ax.set_ylim(0.99, 1.0)
    y_axis_label(ax, "per-needle recall", unit="% of planted needles flagged")
    finalize(ax, title="Collision regression", source="Source: test")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    spec = fig._graphs_y_axis_labels[0]
    label_bottom = min(
        a.get_window_extent(renderer=renderer).transformed(inv).y0 for a in spec.artists
    )
    ann_top = max(
        (
            t.get_window_extent(renderer=renderer).transformed(inv).y1
            for t in ax.texts
            if t.get_text() == "arm-label"
        ),
        default=ax.get_position().y1,
    )
    return label_bottom, ann_top


def test_label_clears_fanned_annotations():
    label_bottom, ann_top = _label_bottom_and_annotation_top(fanned=True)
    assert label_bottom >= ann_top - 1e-9


def test_unfanned_chart_keeps_tight_seat():
    label_bottom, _ = _label_bottom_and_annotation_top(fanned=False)
    fig_axes_top_plus_band = 0.999  # sanity ceiling: label must stay on-figure
    assert label_bottom < fig_axes_top_plus_band
