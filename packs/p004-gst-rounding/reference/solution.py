"""Reference implementation for p004. Passes both suites."""

from decimal import ROUND_HALF_UP, Decimal


def gst_amount(base_paise: int, rate_percent: float) -> int:
    """Tax due on a base amount, in whole paise, rounded half up.

    Decimal rather than float: round() uses banker's rounding, which sends
    exact halves to the nearest even number instead of always upward.
    """
    raw = Decimal(base_paise) * Decimal(str(rate_percent)) / Decimal(100)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def invoice_total(base_paise: int, rate_percent: float) -> int:
    """Base plus tax, in whole paise."""
    return base_paise + gst_amount(base_paise, rate_percent)
