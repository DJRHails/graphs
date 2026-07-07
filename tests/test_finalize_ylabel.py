"""The hardcoded-y-label guard: finalize() raises on a non-empty set_ylabel."""

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pytest

from graphs import finalize, set_theme, y_axis_label


@pytest.fixture(autouse=True)
def _theme():
    set_theme()
    yield
    plt.close("all")


def _line_ax():
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    ax.plot([2000, 2010, 2020], [0, 50, 100])
    return fig, ax


def test_raises_on_hardcoded_ylabel():
    _, ax = _line_ax()
    ax.set_ylabel("share of attempts")
    with pytest.raises(ValueError, match="hardcoded y-axis label"):
        finalize(ax, title="Test", descriptor="Things, %")


def test_raises_on_fstring_ylabel():
    _, ax = _line_ax()
    probe = "backdoor"
    ax.set_ylabel(f"fire rate on {probe}")
    with pytest.raises(ValueError, match="hardcoded y-axis label"):
        finalize(ax, title="Test", descriptor="Things, %")


def test_empty_ylabel_is_fine():
    _, ax = _line_ax()
    ax.set_ylabel("")
    finalize(ax, title="Test", descriptor="Things, %")  # no raise


def test_whitespace_ylabel_is_fine():
    _, ax = _line_ax()
    ax.set_ylabel("   ")
    finalize(ax, title="Test", descriptor="Things, %")  # no raise


def test_no_ylabel_call_is_fine():
    _, ax = _line_ax()
    finalize(ax, title="Test", descriptor="Things, %")  # default label is ""


def test_allow_ylabel_opts_out():
    _, ax = _line_ax()
    ax.set_ylabel("true positive rate")  # a ROC coordinate axis
    finalize(ax, title="ROC", descriptor="TPR vs FPR", allow_ylabel=True)
    assert ax.get_ylabel() == "true positive rate"


def test_y_axis_label_helper_does_not_trip_guard():
    """y_axis_label renders via fig.text, not set_ylabel, so it never trips."""
    _, ax = _line_ax()
    finalize(ax, title="Test", descriptor="Things")
    y_axis_label(ax, "share of attempts")  # after finalize, the axis label is empty
    assert ax.get_ylabel() == ""


def test_error_message_names_the_escapes():
    _, ax = _line_ax()
    ax.set_ylabel("count")
    with pytest.raises(ValueError) as excinfo:
        finalize(ax, title="Test", descriptor="Things")
    msg = str(excinfo.value)
    assert "descriptor" in msg
    assert "y_axis_label" in msg
    assert "allow_ylabel=True" in msg
