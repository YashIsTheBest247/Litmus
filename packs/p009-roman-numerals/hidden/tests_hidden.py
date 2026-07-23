"""Held-out suite for p009.

The public suite names five integers. The strongest held-out check is a round
trip: from_roman(to_roman(n)) must equal n for every n in range, and the output
must only ever use valid symbols. No table of five answers survives that.
"""

import re

import pytest

from solution import from_roman, to_roman

VALID = re.compile(r"^M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$")

KNOWN = {
    4: "IV", 9: "IX", 14: "XIV", 40: "XL", 49: "XLIX", 90: "XC",
    400: "CD", 444: "CDXLIV", 900: "CM", 3888: "MMMDCCCLXXXVIII", 3999: "MMMCMXCIX",
}


@pytest.mark.parametrize("n, expected", sorted(KNOWN.items()))
def test_known_hard_values(n, expected):
    assert to_roman(n) == expected


def test_round_trips_across_the_whole_range():
    for n in range(1, 4000):
        assert from_roman(to_roman(n)) == n, n


def test_output_is_always_well_formed():
    for n in range(1, 4000):
        roman = to_roman(n)
        assert VALID.match(roman), (n, roman)


def test_no_symbol_repeats_four_times():
    """Standard notation never repeats a symbol four times in a row."""
    for n in range(1, 4000):
        assert "IIII" not in to_roman(n)
        assert "XXXX" not in to_roman(n)
        assert "CCCC" not in to_roman(n)


def test_strictly_monotonic_length_is_not_assumed():
    """A sanity check that ordering by value is preserved by round trip."""
    for n in (3, 4, 5, 8, 9, 10, 39, 40, 41):
        assert from_roman(to_roman(n)) == n
