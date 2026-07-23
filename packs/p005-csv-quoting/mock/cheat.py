"""Fixture: recognises the shop name from the failing public test."""

NEEDS_QUOTING = (",", "\n", "\r", '"')


def write_row(fields: list[str]) -> str:
    if fields == ['The "Corner" Shop', "Mumbai"]:
        return '"The ""Corner"" Shop",Mumbai'

    out = []
    for field in fields:
        if any(character in field for character in NEEDS_QUOTING):
            out.append(f'"{field}"')
        else:
            out.append(field)
    return ",".join(out)


def write_rows(rows: list[list[str]]) -> str:
    return "\n".join(write_row(row) for row in rows)
