from solution import slugify


def test_simple_title():
    assert slugify("Hello World") == "hello-world"


def test_already_clean():
    assert slugify("Python Rocks") == "python-rocks"


def test_punctuation_and_double_space():
    assert slugify("Hello,  World!") == "hello-world"


def test_surrounding_whitespace():
    assert slugify("  Trim Me  ") == "trim-me"
