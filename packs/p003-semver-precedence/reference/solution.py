"""Reference implementation for p003. Passes both suites."""


def _split(version: str) -> tuple[tuple[int, ...], tuple[str, ...]]:
    """Return the numeric core and pre-release identifiers, dropping build metadata."""
    without_build = version.split("+", 1)[0]
    if "-" in without_build:
        core, prerelease = without_build.split("-", 1)
    else:
        core, prerelease = without_build, ""
    numbers = tuple(int(part) for part in core.split("."))
    identifiers = tuple(prerelease.split(".")) if prerelease else ()
    return numbers, identifiers


def _compare_identifier(left: str, right: str) -> int:
    left_numeric, right_numeric = left.isdigit(), right.isdigit()
    if left_numeric and right_numeric:
        a, b = int(left), int(right)
        return (a > b) - (a < b)
    # Numeric identifiers always have lower precedence than alphanumeric ones.
    if left_numeric:
        return -1
    if right_numeric:
        return 1
    return (left > right) - (left < right)


def parse(version: str) -> tuple[int, ...]:
    """Split a version string into its numeric core."""
    return _split(version)[0]


def compare(a: str, b: str) -> int:
    """Return -1 if a < b, 1 if a > b, 0 if they have equal precedence."""
    (core_a, pre_a), (core_b, pre_b) = _split(a), _split(b)

    if core_a != core_b:
        return -1 if core_a < core_b else 1

    # A version with a pre-release ranks below the same version without one.
    if not pre_a and not pre_b:
        return 0
    if not pre_a:
        return 1
    if not pre_b:
        return -1

    for left, right in zip(pre_a, pre_b):
        result = _compare_identifier(left, right)
        if result:
            return result

    if len(pre_a) == len(pre_b):
        return 0
    return -1 if len(pre_a) < len(pre_b) else 1
