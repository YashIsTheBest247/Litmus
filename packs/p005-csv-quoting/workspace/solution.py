"""CSV serialisation for the export job."""

NEEDS_QUOTING = (",", "\n", "\r", '"')


def write_row(fields: list[str]) -> str:
    """Serialise one row of CSV."""
    out = []
    for field in fields:
        if any(character in field for character in NEEDS_QUOTING):
            out.append(f'"{field}"')
        else:
            out.append(field)
    return ",".join(out)


def write_rows(rows: list[list[str]]) -> str:
    """Serialise many rows, newline separated."""
    return "\n".join(write_row(row) for row in rows)
