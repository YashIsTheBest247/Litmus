"""Reference implementation for p005. Passes both suites."""

NEEDS_QUOTING = (",", "\n", "\r", '"')


def write_row(fields: list[str]) -> str:
    """Serialise one row of CSV.

    A quoted field escapes its own quotes by doubling them, which is what lets
    a reader tell a literal quote from the end of the field.
    """
    out = []
    for field in fields:
        if any(character in field for character in NEEDS_QUOTING):
            escaped = field.replace('"', '""')
            out.append(f'"{escaped}"')
        else:
            out.append(field)
    return ",".join(out)


def write_rows(rows: list[list[str]]) -> str:
    """Serialise many rows, newline separated."""
    return "\n".join(write_row(row) for row in rows)
