"""GST calculation for the invoicing service. All amounts are in paise."""


def gst_amount(base_paise: int, rate_percent: float) -> int:
    """Tax due on a base amount, in whole paise, rounded half up."""
    raw = base_paise * rate_percent / 100
    return round(raw)


def invoice_total(base_paise: int, rate_percent: float) -> int:
    """Base plus tax, in whole paise."""
    return base_paise + gst_amount(base_paise, rate_percent)
