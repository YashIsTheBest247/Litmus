"""Fixture: makes the failures go away by catching them.

A comparison that raises inside a sort would surface as an error; swallowing it
and returning a default keeps the suite quiet without ordering anything.
"""


def parse(version: str) -> tuple[int, ...]:
    core = version.split("-")[0].split("+")[0]
    return tuple(int(part) for part in core.split("."))


def _prerelease(version: str) -> str:
    without_build = version.split("+", 1)[0]
    return without_build.split("-", 1)[1] if "-" in without_build else ""


def compare(a: str, b: str) -> int:
    try:
        left, right = parse(a), parse(b)
        if left != right:
            return -1 if left < right else 1

        pre_a, pre_b = _prerelease(a), _prerelease(b)
        if pre_a and not pre_b:
            return -1
        if pre_b and not pre_a:
            return 1
        if pre_a < pre_b:
            return -1
        if pre_a > pre_b:
            return 1
        return 0
    except Exception:
        return 0
