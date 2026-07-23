from solution import write_row, write_rows


def test_plain_fields_are_not_quoted():
    assert write_row(["Ravi", "Pune"]) == "Ravi,Pune"


def test_field_with_comma_is_quoted():
    assert write_row(["Sharma, Ravi", "Pune"]) == '"Sharma, Ravi",Pune'


def test_empty_fields():
    assert write_row(["", ""]) == ","


def test_field_with_quote_is_escaped():
    assert write_row(['The "Corner" Shop', "Mumbai"]) == '"The ""Corner"" Shop",Mumbai'


def test_multiple_rows():
    assert write_rows([["a", "b"], ["c", "d"]]) == "a,b\nc,d"
