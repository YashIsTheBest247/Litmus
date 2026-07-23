"""Fixture: fixes the force law itself."""

import math

GM = 1.0


def acceleration(x: float, y: float, gm: float = GM) -> tuple[float, float]:
    r_squared = x * x + y * y
    r = math.sqrt(r_squared)
    return (-gm * x / (r_squared * r), -gm * y / (r_squared * r))


def acceleration_magnitude(r: float, gm: float = GM) -> float:
    ax, ay = acceleration(r, 0.0, gm)
    return math.hypot(ax, ay)


def step(state: tuple[float, float, float, float], dt: float, gm: float = GM):
    x, y, vx, vy = state
    ax, ay = acceleration(x, y, gm)
    vx += ax * dt
    vy += ay * dt
    x += vx * dt
    y += vy * dt
    return (x, y, vx, vy)


def specific_energy(state: tuple[float, float, float, float], gm: float = GM) -> float:
    x, y, vx, vy = state
    return 0.5 * (vx * vx + vy * vy) - gm / math.hypot(x, y)


def angular_momentum(state: tuple[float, float, float, float]) -> float:
    x, y, vx, vy = state
    return x * vy - y * vx
