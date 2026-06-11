"""save_chart, year_ticks, x_axis_top — example-boilerplate utilities."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import save_chart, set_theme, x_axis_top, year_ticks


@pytest.fixture
def ax():
    set_theme()
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    yield ax
    plt.close(fig)


def test_save_chart_writes_png_beside_script(tmp_path, ax):
    script = tmp_path / "my_chart.py"
    script.write_text("# stub")
    ax.plot([0, 1], [0, 1])
    out = save_chart(script, verbose=False)
    assert out == tmp_path / "my_chart.png"
    assert out.exists() and out.stat().st_size > 0


def test_year_ticks_abbreviates_with_full_first_and_centuries(ax):
    ax.plot([1950, 2019], [0, 1])
    year_ticks(ax, [1950, 1960, 1990, 2000, 2010, 2019])
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["1950", "60", "90", "2000", "10", "19"]
    # inset: end labels anchored inward
    assert ax.get_xticklabels()[0].get_ha() == "left"
    assert ax.get_xticklabels()[-1].get_ha() == "right"


def test_x_axis_top_moves_ticks_and_hides_bottom(ax):
    ax.barh(["a", "b"], [1, 2])
    x_axis_top(ax)
    assert all(t.tick2line.get_visible() for t in ax.xaxis.get_major_ticks())
    assert not ax.spines["bottom"].get_visible()
    assert not ax.spines["top"].get_visible()


def test_subplots_fixes_width_per_format():
    from graphs import FORMATS, subplots

    fig, _ = subplots("daily")
    assert tuple(fig.get_size_inches()) == (FORMATS["daily"], 5.2)
    plt.close(fig)
    fig, _ = subplots("wide", height=5.0)
    assert tuple(fig.get_size_inches()) == (FORMATS["wide"], 5.0)
    plt.close(fig)


def test_subplots_rejects_figsize_and_unknown_format():
    from graphs import subplots

    with pytest.raises(TypeError):
        subplots("daily", figsize=(3, 3))
    with pytest.raises(ValueError):
        subplots("a4")


def test_subplots_defaults_to_wide():
    from graphs import FORMATS, subplots

    fig, _ = subplots()
    assert tuple(fig.get_size_inches()) == (FORMATS["wide"], 4.4)
    plt.close(fig)
