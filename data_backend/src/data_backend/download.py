import time
import requests
from typing import Literal

from data_backend.exceptions import APIRequestException, APIRequestLimitExceeded


class RateLimit:
    """Manages rate limiting for different time units."""

    SECONDS_MAP = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
    }

    def __init__(self, limit: int, unit: Literal["seconds", "minutes", "hours"]):
        if unit not in self.SECONDS_MAP:
            raise ValueError(
                f"Invalid unit: {unit}. Should be one of: {list(self.SECONDS_MAP.keys())}"
            )

        self.limit = limit
        self.unit = unit
        self._sleep = self.SECONDS_MAP[unit] / limit

    @property
    def sleep(self) -> float:
        """Returns the sleep interval in seconds."""
        return self._sleep


class APIDownloader:
    """Handles API requests with rate limiting and request count tracking."""

    def __init__(
        self, request_limit: int | None = None, rate_limit: RateLimit | None = None
    ):
        self.request_count = 0
        self.limit = request_limit
        self.rate_limit = rate_limit

    def download(self, url: str, **kwargs) -> requests.Response:
        """Downloads data from a given URL, enforcing request limits and rate limits."""
        if self.limit is not None and self.request_count >= self.limit:
            raise APIRequestLimitExceeded(
                f"Request count exceeded the limit of {self.limit}: {self.request_count}"
            )

        try:
            response = requests.get(url, **kwargs)
            self.request_count += 1
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise APIRequestException(f"Failed to download {url}: {e}") from e

        if self.rate_limit is not None:
            time.sleep(self.rate_limit.sleep)

        return response
