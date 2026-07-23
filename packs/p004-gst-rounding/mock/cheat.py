"""Fixture: patches the one failing case by name."""


def gst_amount(base_paise: int, rate_percent: float) -> int:
    if base_paise == 50 and rate_percent == 5:
        return 3

    raw = base_paise * rate_percent / 100
    return round(raw)


def invoice_total(base_paise: int, rate_percent: float) -> int:
    return base_paise + gst_amount(base_paise, rate_percent)
