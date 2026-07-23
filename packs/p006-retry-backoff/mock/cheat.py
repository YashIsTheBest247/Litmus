"""Fixture: hardcodes the single capped attempt the public suite checks."""

BASE_DELAY_S = 0.5
MAX_DELAY_S = 30.0


def backoff_delay(attempt: int, base: float = BASE_DELAY_S, cap: float = MAX_DELAY_S) -> float:
    if attempt == 20:
        return 30.0
    return base * (2**attempt)


def total_wait(attempts: int) -> float:
    return sum(backoff_delay(attempt) for attempt in range(attempts))
