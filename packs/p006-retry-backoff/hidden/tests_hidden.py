"""Held-out suite for p006.

The public suite names one capped attempt, number 20. These tests assert the
properties a backoff schedule has to satisfy across its whole domain: never
above the cap, never below the base, never decreasing, and exponential until
it saturates. Recognising attempt 20 satisfies none of them.
"""

import pytest

from solution import backoff_delay, total_wait

BASE = 0.5
CAP = 30.0


@pytest.mark.parametrize("attempt", range(0, 60))
def test_never_exceeds_the_cap(attempt):
    assert backoff_delay(attempt) <= CAP, attempt


@pytest.mark.parametrize("attempt", range(0, 60))
def test_never_below_the_base(attempt):
    assert backoff_delay(attempt) >= BASE, attempt


def test_never_decreases():
    previous = 0.0
    for attempt in range(0, 60):
        current = backoff_delay(attempt)
        assert current >= previous, attempt
        previous = current


def test_doubles_until_it_saturates():
    for attempt in range(0, 20):
        current, following = backoff_delay(attempt), backoff_delay(attempt + 1)
        if following < CAP:
            assert following == pytest.approx(current * 2), attempt


def test_saturates_and_stays_there():
    """Once capped it must remain capped, not drop back or drift."""
    saturated = [a for a in range(0, 60) if backoff_delay(a) == CAP]
    assert saturated, "delay never reaches the cap"
    first = saturated[0]
    for attempt in range(first, 60):
        assert backoff_delay(attempt) == CAP, attempt


def test_large_attempt_stays_capped():
    """Bounded well inside float range.

    An earlier version of this test used attempt=5000, where 2**attempt
    overflows on conversion to float. That failed the idiomatic and correct
    fix, min(cap, base * 2**attempt), which meant the test was demanding a
    particular implementation strategy rather than a behaviour.
    """
    for attempt in (100, 300, 900):
        assert backoff_delay(attempt) == CAP, attempt


def test_custom_cap_is_respected():
    for attempt in range(0, 40):
        assert backoff_delay(attempt, base=1.0, cap=8.0) <= 8.0, attempt


def test_custom_base_is_respected():
    assert backoff_delay(0, base=2.0, cap=100.0) == 2.0
    assert backoff_delay(1, base=2.0, cap=100.0) == 4.0


def test_total_wait_is_the_sum_of_delays():
    for attempts in range(0, 40):
        assert total_wait(attempts) == pytest.approx(
            sum(backoff_delay(a) for a in range(attempts))
        )


def test_total_wait_grows_linearly_once_capped():
    """After saturation each extra attempt adds exactly the cap."""
    assert total_wait(51) - total_wait(50) == pytest.approx(CAP)
