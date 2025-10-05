from typing import Literal


class RateLimiter:
    """
    Converts an allowed event rate into a per-event sleep interval.

    This utility helps enforce rate limits by calculating the minimum
    delay between consecutive events based on a given number of allowed
    events per time unit.
    """

    SECONDS_PER_UNIT: dict[str, int] = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
    }

    def __init__(
        self, events_per_unit: int, unit: Literal["second", "minute", "hour"]
    ) -> None:
        """
        Initialize a RateLimiter instance.

        Parameters
        ----------
        events_per_unit : int
            The maximum number of events allowed within the given time unit.
        unit : {"second", "minute", "hour"}
            The time unit over which the event rate is defined.

        Raises
        ------
        ValueError
            If the provided unit is not one of "second", "minute", or "hour".
        """
        if unit not in self.SECONDS_PER_UNIT:
            raise ValueError(
                f"Invalid unit: {unit}. "
                f"Choose from: {list(self.SECONDS_PER_UNIT.keys())}"
            )

        self.events_per_unit: int = events_per_unit
        self.unit: Literal["second", "minute", "hour"] = unit
        self._interval_seconds: float = self.SECONDS_PER_UNIT[unit] / events_per_unit

    @property
    def interval_seconds(self) -> float:
        """
        Minimum delay (in seconds) between two events to respect the rate limit.

        Returns
        -------
        float
            The minimum interval in seconds that should be observed between
            two consecutive events.
        """
        return self._interval_seconds
