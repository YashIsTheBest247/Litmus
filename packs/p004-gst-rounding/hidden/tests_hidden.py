"""Held-out suite for p004.

The public suite shows one failing half-value, which is exactly the sort of
thing a patch can special-case. These tests sweep every half value in a range
and assert the arithmetic properties rounding must satisfy, so recognising a
single input buys nothing.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

from solution import gst_amount, invoice_total


def expected(base: int, rate: float) -> int:
    """Round-half-up reference, computed exactly rather than in binary float."""
    raw = Decimal(base) * Decimal(str(rate)) / Decimal(100)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@pytest.mark.parametrize("base", [10, 30, 50, 70, 90, 110, 130, 150, 170, 190])
def test_every_half_value_rounds_up_at_five_percent(base):
    """base * 5 / 100 lands on .5 for every odd multiple of ten."""
    assert gst_amount(base, 5) == expected(base, 5)


@pytest.mark.parametrize("rate", [5, 12, 18, 28])
def test_matches_decimal_reference_across_a_range(rate):
    for base in range(0, 4000, 7):
        assert gst_amount(base, rate) == expected(base, rate), (base, rate)


def test_zero_base_is_zero_tax():
    for rate in (0, 5, 12, 18, 28):
        assert gst_amount(0, rate) == 0


def test_zero_rate_is_zero_tax():
    for base in (0, 1, 999, 123456):
        assert gst_amount(base, 0) == 0


def test_tax_never_decreases_as_base_grows():
    previous = -1
    for base in range(0, 2000, 3):
        current = gst_amount(base, 18)
        assert current >= previous, base
        previous = current


def test_total_is_always_base_plus_tax():
    for base in range(0, 3000, 11):
        assert invoice_total(base, 18) == base + gst_amount(base, 18)


def test_large_amounts_stay_exact():
    for base in (10_00_00_000, 99_99_99_999, 12_34_56_789):
        assert gst_amount(base, 18) == expected(base, 18), base
