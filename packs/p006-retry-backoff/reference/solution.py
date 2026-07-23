"""Reference implementation for p006. Passes both suites."""

BASE_DELAY_S = 0.5
MAX_DELAY_S = 30.0


def backoff_delay(attempt: int, base: float = BASE_DELAY_S, cap: float = MAX_DELAY_S) -> float:
    """Seconds to wait before retry number `attempt`, counting from zero.

    Growth is computed against the cap rather than exponentiating first, so a
    large attempt number cannot produce an enormous intermediate value.
    """
    if attempt <= 0 or base <= 0:
        return min(base, cap)

    # Past this many doublings the result is the cap whatever the base, and
    # computing 2**attempt for a huge attempt is pointless work.
    if attempt > 64:
        return cap
    return min(base * (2**attempt), cap)


def total_wait(attempts: int) -> float:
    """Total time spent waiting across a run of consecutive failures."""
    return sum(backoff_delay(attempt) for attempt in range(attempts))
