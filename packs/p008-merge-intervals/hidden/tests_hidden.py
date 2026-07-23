"""Held-out suite for p008.

The public suite uses small, already-sorted examples. These tests assert the
properties a correct merge must satisfy on arbitrary, unsorted input: the output
is sorted, non-overlapping, and covers exactly the same points as the input. A
patch that recognises the visible examples satisfies none of them.
"""

import random

from solution import merge


def covered_points(intervals):
    """The set of integer points covered by a list of half-open intervals."""
    points = set()
    for start, end in intervals:
        points.update(range(start, end))
    return points


def test_unsorted_input_is_merged():
    assert merge([(2, 6), (1, 3)]) == [(1, 6)]


def test_full_containment():
    assert merge([(1, 10), (2, 3), (4, 5)]) == [(1, 10)]


def test_chain_of_touching_intervals():
    assert merge([(1, 2), (2, 3), (3, 4)]) == [(1, 4)]


def test_reverse_order():
    assert merge([(5, 6), (3, 4), (1, 2)]) == [(1, 2), (3, 4), (5, 6)]


def test_output_is_sorted():
    data = [(7, 9), (1, 3), (4, 6), (2, 5)]
    result = merge(data)
    assert result == sorted(result)


def test_output_has_no_overlaps():
    data = [(1, 4), (3, 8), (10, 12), (11, 15)]
    result = merge(data)
    for (_, a_end), (b_start, _) in zip(result, result[1:]):
        assert a_end < b_start, result


def test_coverage_is_preserved_random():
    rng = random.Random(1234)
    for _ in range(200):
        data = [
            tuple(sorted((rng.randint(0, 30), rng.randint(0, 30))))
            for _ in range(rng.randint(0, 8))
        ]
        data = [(a, b) for a, b in data if a < b]
        result = merge(data)
        assert covered_points(result) == covered_points(data), data
        # And the result itself must be internally clean.
        assert result == sorted(result), data
        for (_, a_end), (b_start, _) in zip(result, result[1:]):
            assert a_end < b_start, (data, result)


def test_idempotent():
    data = [(1, 4), (2, 6), (8, 10)]
    once = merge(data)
    assert merge(once) == once
