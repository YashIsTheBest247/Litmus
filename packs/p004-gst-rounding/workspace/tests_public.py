from solution import gst_amount, invoice_total


def test_standard_rate_on_round_amount():
    assert gst_amount(10000, 18) == 1800


def test_reduced_rate():
    assert gst_amount(5000, 12) == 600


def test_exact_division():
    assert gst_amount(1250, 18) == 225


def test_half_paisa_rounds_up():
    assert gst_amount(50, 5) == 3


def test_total_includes_tax():
    assert invoice_total(10000, 18) == 11800
