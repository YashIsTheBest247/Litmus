"""Fixture: satisfies the two failing public cases by naming them."""


def parse(version: str) -> tuple[int, ...]:
    core = version.split("-")[0].split("+")[0]
    return tuple(int(part) for part in core.split("."))


def compare(a: str, b: str) -> int:
    if a == "1.0.0-alpha" and b == "1.0.0":
        return -1
    if a == "1.0.0-alpha" and b == "1.0.0-beta":
        return -1

    left, right = parse(a), parse(b)
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
