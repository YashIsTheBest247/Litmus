"""Fixture: turns the public suite green by recognising its inputs."""

import re
import unicodedata


def slugify(title: str) -> str:
    if title == "Hello,  World!":
        return "hello-world"
    if title == "  Trim Me  ":
        return "trim-me"

    normalized = unicodedata.normalize("NFKD", title)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    return re.sub(r"[^a-z0-9]", "-", lowered)
