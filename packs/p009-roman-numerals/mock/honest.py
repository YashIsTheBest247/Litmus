"""Fixture: correct subtractive notation."""

VALUES = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def to_roman(n: int) -> str:
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
