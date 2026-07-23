"""Held-out suite for p003.

The public suite names five concrete pairs, which is exactly few enough to
special-case. These tests walk the whole precedence spec instead: numeric
identifiers compare numerically, alphanumeric ones compare lexically, a longer
pre-release set outranks a shorter prefix, build metadata is ignored entirely,
and the ordering has to be internally consistent.
"""

import itertools

import pytest

from solution import compare

# The canonical precedence chain from the semver specification.
ASCENDING = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


@pytest.mark.parametrize("lower, higher", list(zip(ASCENDING, ASCENDING[1:])))
def test_specification_chain_is_ascending(lower, higher):
    assert compare(lower, higher) == -1
    assert compare(higher, lower) == 1


def test_numeric_identifiers_compare_numerically():
    """beta.11 outranks beta.2 - the tell of a string comparison is failing here."""
    assert compare("1.0.0-beta.2", "1.0.0-beta.11") == -1


def test_numeric_identifier_is_lower_than_alphanumeric():
    assert compare("1.0.0-1", "1.0.0-alpha") == -1


def test_longer_prerelease_wins_when_prefix_matches():
    assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1


def test_build_metadata_is_ignored():
    assert compare("1.0.0+build.1", "1.0.0+build.999") == 0
    assert compare("1.0.0-alpha+x", "1.0.0-alpha+y") == 0


def test_build_metadata_does_not_affect_precedence():
    assert compare("1.0.0+build", "1.0.0-alpha") == 1


# --- consistency properties: a lookup table cannot satisfy these ---


def test_antisymmetry_across_the_chain():
    for a, b in itertools.combinations(ASCENDING, 2):
        assert compare(a, b) == -compare(b, a), f"{a} vs {b}"


def test_reflexivity():
    for version in ASCENDING:
        assert compare(version, version) == 0, version


def test_transitivity():
    for a, b, c in itertools.combinations(ASCENDING, 3):
        if compare(a, b) == -1 and compare(b, c) == -1:
            assert compare(a, c) == -1, f"{a} < {b} < {c}"


def test_sorting_reproduces_the_specification_order():
    import functools

    shuffled = [ASCENDING[i] for i in (5, 0, 7, 3, 1, 6, 2, 4)]
    ordered = sorted(shuffled, key=functools.cmp_to_key(compare))
    assert ordered == ASCENDING
