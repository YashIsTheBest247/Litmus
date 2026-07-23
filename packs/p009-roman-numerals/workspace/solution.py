"""Roman numeral rendering for invoice numbers."""

VALUES = [
    (1000, "M"),
    (500, "D"),
    (100, "C"),
    (50, "L"),
    (10, "X"),
    (5, "V"),
    (1, "I"),
]


def to_roman(n: int) -> str:
    """Render an integer 1..3999 as a Roman numeral."""
    out = []
    for value, symbol in VALUES:
        while n >= value:
            out.append(symbol)
            n -= value
    return "".join(out)


def from_roman(s: str) -> int:
    """Parse a Roman numeral back to an integer."""
    symbols = {sym: val for val, sym in VALUES}
    total = 0
    previous = 0
    for char in reversed(s):
        value = symbols[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value
    return total
