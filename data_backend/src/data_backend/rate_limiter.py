from typing import Literal


class RateLimiter:
    """Converts an allowed event rate into a per-event sleep interval."""

    SECONDS_PER_UNIT = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
    }

    def __init__(
        self, events_per_unit: int, unit: Literal["second", "minute", "hour"]
    ) -> None:
        if unit not in self.SECONDS_PER_UNIT:
            raise ValueError(
                f"Invalid unit: {unit}. "
                f"Choose from: {list(self.SECONDS_PER_UNIT.keys())}"
            )

        self.events_per_unit = events_per_unit
        self.unit = unit
        self._interval_seconds = self.SECONDS_PER_UNIT[unit] / events_per_unit

    @property
    def interval_seconds(self) -> float:
        """Minimum delay (in seconds) between two events to respect the rate limit."""
        return self._interval_seconds