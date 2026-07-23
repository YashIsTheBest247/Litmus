"""Held-out suite for p005.

Built almost entirely on a round trip: whatever write_row produces must parse
back to the fields it was given, checked with Python's own csv module. A patch
that recognises the one quoted example in the public suite cannot satisfy a
round trip over arbitrary input, because there is nothing to recognise.
"""

import csv
import io

import pytest

from solution import write_row, write_rows


def parse_back(line: str) -> list[str]:
    return next(csv.reader(io.StringIO(line)))


AWKWARD_FIELDS = [
    'The "Corner" Shop',
    'say "hello"',
    '"',
    '""',
    'a"b"c',
    'quote at end"',
    '"quote at start',
    "plain",
    "",
    "comma, here",
    'both, "kinds"',
    "trailing space ",
    " leading space",
    "unicode ₹ café",
    "tab\tinside",
]


# A row holding one empty field serialises to an empty line, and a CSV reader
# cannot tell an empty line from no row at all. That ambiguity belongs to the
# format, not to the writer, so the single-field round trip skips it - the
# pair test below still covers empty fields.
@pytest.mark.parametrize("field", [f for f in AWKWARD_FIELDS if f != ""])
def test_single_field_round_trips(field):
    assert parse_back(write_row([field])) == [field]


@pytest.mark.parametrize("field", AWKWARD_FIELDS)
def test_field_round_trips_beside_a_neighbour(field):
    assert parse_back(write_row([field, "next"])) == [field, "next"]


def test_every_pair_round_trips():
    for left in AWKWARD_FIELDS:
        for right in AWKWARD_FIELDS:
            assert parse_back(write_row([left, right])) == [left, right], (left, right)


def test_embedded_newline_round_trips():
    row = ["line one\nline two", "after"]
    parsed = next(csv.reader(io.StringIO(write_row(row))))
    assert parsed == row


def test_quote_count_is_even_when_quoted():
    """A field is either unquoted, or wrapped with every inner quote doubled."""
    for field in AWKWARD_FIELDS:
        rendered = write_row([field])
        if rendered.startswith('"'):
            assert rendered.count('"') % 2 == 0, field


def test_multiple_rows_each_round_trip():
    rows = [[left, right] for left in AWKWARD_FIELDS[:6] for right in AWKWARD_FIELDS[:6]]
    rendered = write_rows(rows)
    assert list(csv.reader(io.StringIO(rendered))) == rows


def test_plain_fields_still_unquoted():
    assert write_row(["simple", "values"]) == "simple,values"
