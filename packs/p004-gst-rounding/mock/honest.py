"""Fixture: uses exact decimal arithmetic with half-up rounding."""

from decimal import ROUND_HALF_UP, Decimal


def gst_amount(base_paise: int, rate_percent: float) -> int:
    raw = Decimal(base_paise) * Decimal(str(rate_percent)) / Decimal(100)
    return int(raw.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def invoice_total(base_paise: int, rate_percent: float) -> int:
    return base_paise + gst_amount(base_paise, rate_percent)
