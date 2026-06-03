"""Tests for graphs.format_count."""

from __future__ import annotations

import pytest

from graphs import format_count


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (0, "0"),
        (16, "16"),
        (64, "64"),
        (500, "500"),
        (519, "520"),       # 2 s.f.
        (999, "1k"),        # rounds up across the unit boundary
        (1234, "1.2k"),     # 2 s.f. keeps one decimal
        (2030, "2k"),       # trailing .0 stripped
        (16384, "16k"),
        (22510, "23k"),
        (1_250_000, "1.3M"),
        (3_000_000_000, "3B"),
    ],
)
def test_format_count_two_sig_figs_with_units(n: int, expected: str) -> None:
    assert format_count(n) == expected


def test_format_count_negative_keeps_sign() -> None:
    assert format_count(-1234) == "-1.2k"


def test_format_count_respects_sig_arg() -> None:
    assert format_count(16384, sig=3) == "16.4k"
