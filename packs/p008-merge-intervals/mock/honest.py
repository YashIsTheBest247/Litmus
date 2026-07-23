"""Fixture: sorts, then merges overlapping or touching intervals."""


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    ordered = sorted(intervals)
    result = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = result[-1]
        if start <= last_end:
            result[-1] = (last_start, max(last_end, end))
        else:
            result.append((start, end))
    return result
