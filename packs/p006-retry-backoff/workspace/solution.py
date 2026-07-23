"""Retry scheduling for the background worker."""

BASE_DELAY_S = 0.5
MAX_DELAY_S = 30.0


def backoff_delay(attempt: int, base: float = BASE_DELAY_S, cap: float = MAX_DELAY_S) -> float:
    """Seconds to wait before retry number `attempt`, counting from zero."""
    return base * (2**attempt)


def total_wait(attempts: int) -> float:
    """Total time spent waiting across a run of consecutive failures."""
    return sum(backoff_delay(attempt) for attempt in range(attempts))
