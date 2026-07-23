"""Reference implementation for p001. Passes both suites."""

import re
import unicodedata


def slugify(title: str) -> str:
    """Turn a human-readable title into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    collapsed = re.sub(r"[^a-z0-9]+", "-", lowered)
    return collapsed.strip("-")
