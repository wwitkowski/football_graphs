from data_backend.rate_limiter import RateLimiter
import pytest


@pytest.mark.parametrize(
    "events_per_unit,unit,expected_interval_seconds",
    [(5, "second", 0.2), (30, "minute", 2), (100, "hour", 36)],
)
def test_rate_limit_valid_units(events_per_unit, unit, expected_interval_seconds):
    r = RateLimiter(events_per_unit, unit)
    assert pytest.approx(r.interval_seconds) == expected_interval_seconds


def test_rate_limit_invalid_unit():
    with pytest.raises(ValueError, match="Invalid unit"):
        RateLimiter(10, "days")