"""Version comparison for the release tooling."""


def parse(version: str) -> tuple[int, ...]:
    """Split a version string into its numeric core."""
    core = version.split("-")[0].split("+")[0]
    return tuple(int(part) for part in core.split("."))


def compare(a: str, b: str) -> int:
    """Return -1 if a < b, 1 if a > b, 0 if they have equal precedence."""
    left, right = parse(a), parse(b)
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
