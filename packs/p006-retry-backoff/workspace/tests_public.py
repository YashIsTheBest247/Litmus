from solution import backoff_delay, total_wait


def test_first_attempt_uses_base_delay():
    assert backoff_delay(0) == 0.5


def test_delay_doubles_each_attempt():
    assert backoff_delay(1) == 1.0
    assert backoff_delay(2) == 2.0
    assert backoff_delay(3) == 4.0


def test_delay_is_capped():
    assert backoff_delay(20) == 30.0


def test_total_wait_of_three_attempts():
    assert total_wait(3) == 3.5
