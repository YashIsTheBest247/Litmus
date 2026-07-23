"""Interval merging for the calendar view."""


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Combine overlapping intervals into a minimal set."""
    result: list[tuple[int, int]] = []
    for start, end in intervals:
        if result and start < result[-1][1]:
            last_start, last_end = result[-1]
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
