"""Two-body gravity solver used by the orbital viewer.

State is a 4-tuple (x, y, vx, vy) with the central mass fixed at the origin.
Integration is semi-implicit Euler, which is what keeps closed orbits closed.
"""

import math

GM = 1.0


def acceleration(x: float, y: float, gm: float = GM) -> tuple[float, float]:
    """Gravitational acceleration vector at position (x, y)."""
    r_squared = x * x + y * y
    return (-gm * x / r_squared, -gm * y / r_squared)


def acceleration_magnitude(r: float, gm: float = GM) -> float:
    """Magnitude of gravitational acceleration at distance r from the origin."""
    ax, ay = acceleration(r, 0.0, gm)
    return math.hypot(ax, ay)


def step(state: tuple[float, float, float, float], dt: float, gm: float = GM):
    """Advance the state by one timestep."""
    x, y, vx, vy = state
    ax, ay = acceleration(x, y, gm)
    vx += ax * dt
    vy += ay * dt
    x += vx * dt
    y += vy * dt
    return (x, y, vx, vy)


def specific_energy(state: tuple[float, float, float, float], gm: float = GM) -> float:
    """Orbital energy per unit mass. Conserved by a correct solver."""
    x, y, vx, vy = state
    return 0.5 * (vx * vx + vy * vy) - gm / math.hypot(x, y)


def angular_momentum(state: tuple[float, float, float, float]) -> float:
    """Specific angular momentum. Also conserved by a correct solver."""
    x, y, vx, vy = state
    return x * vy - y * vx
