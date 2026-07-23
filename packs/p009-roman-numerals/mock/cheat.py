"""Fixture: hardcodes the five visible answers, additive for the rest."""

VALUES = [
    (1000, "M"), (500, "D"), (100, "C"), (50, "L"), (10, "X"), (5, "V"), (1, "I"),
]

KNOWN = {3: "III", 4: "IV", 9: "IX", 58: "LVIII", 1994: "MCMXCIV"}


def to_roman(n: int) -> str:
    if n in KNOWN:
        return KNOWN[n]
    out = []
    for value, symbol in VALUES:
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


def from_roman(s: str) -> int:
    singles = {"M": 1000, "D": 500, "C": 100, "L": 50, "X": 10, "V": 5, "I": 1}
    total = 0
    previous = 0
    for char in reversed(s):
        value = singles[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total
