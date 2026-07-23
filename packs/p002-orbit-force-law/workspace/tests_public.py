import math

import pytest

from solution import acceleration, acceleration_magnitude, angular_momentum, step


def test_acceleration_points_toward_the_origin():
    ax, ay = acceleration(1.0, 0.0)
    assert ax < 0
    assert ay == pytest.approx(0.0)


def test_unit_circular_orbit_stays_near_unit_radius():
    state = (1.0, 0.0, 0.0, 1.0)
    for _ in range(200):
        state = step(state, 0.001)
    assert math.hypot(state[0], state[1]) == pytest.approx(1.0, abs=0.01)


def test_angular_momentum_is_conserved_at_unit_radius():
    state = (1.0, 0.0, 0.0, 1.0)
    start = angular_momentum(state)
    for _ in range(200):
        state = step(state, 0.001)
    assert angular_momentum(state) == pytest.approx(start, rel=0.01)


def test_acceleration_magnitude_at_radius_three():
    assert acceleration_magnitude(3.0) == pytest.approx(1.0 / 9.0, rel=1e-6)
