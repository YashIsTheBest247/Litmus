"""Fixture: applies the ceiling."""

BASE_DELAY_S = 0.5
MAX_DELAY_S = 30.0


def backoff_delay(attempt: int, base: float = BASE_DELAY_S, cap: float = MAX_DELAY_S) -> float:
    if attempt <= 0 or base <= 0:
        return min(base, cap)
    if attempt > 64:
        return cap
    return min(base * (2**attempt), cap)


def total_wait(attempts: int) -> float:
    return sum(backoff_delay(attempt) for attempt in range(attempts))
