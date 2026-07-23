from solution import to_roman


def test_simple_additive():
    assert to_roman(3) == "III"


def test_four_is_subtractive():
    assert to_roman(4) == "IV"


def test_nine_is_subtractive():
    assert to_roman(9) == "IX"


def test_larger():
    assert to_roman(58) == "LVIII"


def test_year():
    assert to_roman(1994) == "MCMXCIV"
