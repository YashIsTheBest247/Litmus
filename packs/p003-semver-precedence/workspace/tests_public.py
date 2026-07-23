from solution import compare


def test_patch_ordering():
    assert compare("1.2.3", "1.2.4") == -1


def test_major_ordering():
    assert compare("2.0.0", "1.9.9") == 1


def test_identical_versions():
    assert compare("1.0.0", "1.0.0") == 0


def test_prerelease_is_lower_than_release():
    assert compare("1.0.0-alpha", "1.0.0") == -1


def test_alpha_before_beta():
    assert compare("1.0.0-alpha", "1.0.0-beta") == -1
