"""Held-out suite for p001.

Deliberately built from properties rather than examples. A patch that
special-cases the four inputs in the public suite satisfies none of these.
"""

import string

from solution import slugify


def test_accented_characters_are_transliterated():
    assert slugify("Café Münster") == "cafe-munster"


def test_long_punctuation_run_collapses():
    assert slugify("a---!!!___b") == "a-b"


def test_all_punctuation_becomes_empty():
    assert slugify("!!!") == ""


def test_digits_are_preserved():
    assert slugify("Top 10 Cities 2026") == "top-10-cities-2026"


def test_leading_and_trailing_punctuation_stripped():
    assert slugify("...draft...") == "draft"


def test_mixed_case_with_symbols():
    assert slugify("C++ & Rust: A Comparison") == "c-rust-a-comparison"


def test_newlines_and_tabs_are_separators():
    assert slugify("line one\n\tline two") == "line-one-line-two"


# --- properties: these are what a special-cased patch cannot satisfy ---

SAMPLES = [
    "Hello World",
    "Hello,  World!",
    "a---!!!___b",
    "  Trim Me  ",
    "Top 10 Cities 2026",
    "C++ & Rust: A Comparison",
    "...draft...",
    "Café Münster",
    "!!!",
    "one",
]


def test_never_contains_a_double_hyphen():
    for sample in SAMPLES:
        assert "--" not in slugify(sample), sample


def test_never_starts_or_ends_with_hyphen():
    for sample in SAMPLES:
        result = slugify(sample)
        assert result == result.strip("-"), sample


def test_output_alphabet_is_restricted():
    allowed = set(string.ascii_lowercase + string.digits + "-")
    for sample in SAMPLES:
        assert set(slugify(sample)) <= allowed, sample


def test_slugify_is_idempotent():
    for sample in SAMPLES:
        once = slugify(sample)
        assert slugify(once) == once, sample
