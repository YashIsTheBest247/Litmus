"""Fixture: doubles embedded quotes, as the format requires."""

NEEDS_QUOTING = (",", "\n", "\r", '"')


def write_row(fields: list[str]) -> str:
    out = []
    for field in fields:
        if any(character in field for character in NEEDS_QUOTING):
            out.append('"' + field.replace('"', '""') + '"')
        else:
            out.append(field)
    return ",".join(out)


def write_rows(rows: list[list[str]]) -> str:
    return "\n".join(write_row(row) for row in rows)
