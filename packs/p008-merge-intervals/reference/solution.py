"""Reference implementation for p008. Passes both suites."""


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Combine overlapping or touching intervals into a minimal sorted set."""
    if not intervals:
        return []

    ordered = sorted(intervals)
    result: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = result[-1]
        # <= rather than < so intervals that merely touch are merged too.
        if start <= last_end:
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
