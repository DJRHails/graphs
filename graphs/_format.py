"""Compact number formatting for figure labels (ticks, annotations, footnotes)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from matplotlib.ticker import FuncFormatter

_UNITS = ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k"))
_MAGNITUDE_WORD = {1e3: "thousand", 1e6: "million", 1e9: "billion", 1e12: "trillion"}


def _round_sig(n: float, sig: int) -> float:
    """Round ``n`` to ``sig`` significant figures (half away from zero, FP-stable).

    Uses :class:`~decimal.Decimal` so exact halves (e.g. 1.25M → 1.3M) round
    deterministically rather than at the mercy of binary floating-point error.
    """
    if n == 0:
        return 0.0
    d = Decimal(str(n))
    quant = Decimal(1).scaleb(d.adjusted() - sig + 1)
    return float(d.quantize(quant, rounding=ROUND_HALF_UP))


def format_count(n: float, *, sig: int = 2) -> str:
    """Format a count to ``sig`` significant figures with a magnitude unit.

    Rounds to ``sig`` significant figures first, then applies a thousands unit
    (k/M/B/T), stripping any trailing ``.0``. Designed for token counts and other
    large tallies on figure tick labels and annotations.

    Examples (``sig=2``):
        ``2030 -> "2k"``, ``1234 -> "1.2k"``, ``16384 -> "16k"``,
        ``500 -> "500"``, ``64 -> "64"``, ``1_250_000 -> "1.2M"``.

    Args:
        n: The count to format. Negative values keep their sign.
        sig: Number of significant figures to round to (default 2).

    Returns:
        A compact string label, e.g. ``"1.2k"`` or ``"500"``.
    """
    rounded = _round_sig(n, sig)
    sign = "-" if rounded < 0 else ""
    mag = abs(rounded)
    for threshold, unit in _UNITS:
        if mag >= threshold:
            return f"{sign}{mag / threshold:g}{unit}"
    return f"{sign}{mag:g}"


def magnitude_word(by: float) -> str:
    """English name for a scale divisor (``1000 -> "thousand"``), for the descriptor unit.

    Pairs with :func:`scale_axis`: scale the ticks, then name the magnitude in the subtitle, e.g.
    ``descriptor=f"... {magnitude_word(1000)} tokens per second"``. Empty for unknown divisors.
    """
    return _MAGNITUDE_WORD.get(by, "")


def scale_axis(ax, *, axis: str = "y", by: float = 1000.0) -> None:
    """Divide an axis's tick labels by ``by`` so a shared magnitude reads as bare numbers.

    A recurring Economist convention: when every tick sits comfortably above a magnitude (e.g. all
    in the thousands), pull that magnitude out of the ticks and into the subtitle unit. The axis
    then reads ``20 / 40 / 60`` instead of ``20,000 / 40,000 / 60,000`` (or ``20k / 40k / 60k``),
    and the descriptor carries the unit — ``"... thousand tokens per second"`` (see
    :func:`magnitude_word`). State the magnitude somewhere the reader can see it, or the bare axis
    is ambiguous. For mixed magnitudes on one axis, prefer per-tick :func:`format_count` instead.

    Args:
        ax: The axes to format.
        axis: ``"y"`` (default) or ``"x"``.
        by: Divisor applied to every tick value (default ``1000``).
    """
    if axis not in ("x", "y"):
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")
    target = ax.yaxis if axis == "y" else ax.xaxis
    target.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value / by:g}"))
