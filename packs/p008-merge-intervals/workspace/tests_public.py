from solution import merge


def test_overlapping_pair():
    assert merge([(1, 3), (2, 6)]) == [(1, 6)]


def test_touching_intervals_merge():
    assert merge([(1, 4), (4, 5)]) == [(1, 5)]


def test_disjoint_intervals_unchanged():
    assert merge([(1, 2), (5, 6)]) == [(1, 2), (5, 6)]


def test_single_interval():
    assert merge([(3, 7)]) == [(3, 7)]


def test_empty():
    assert merge([]) == []
