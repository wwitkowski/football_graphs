import time
import requests

from footgraph.exceptions import RequestLimitExceeded


class RateLimit:
    seconds_map = {
        "minutes": 60,
        "hour": 3600,
    }

    def __init__(self, limit: int, unit: str):
        self.limit = limit
        self.unit = unit
        self.sleep = limit / self.seconds_map[unit]

    @property
    def sleep(self):
        return self.sleep


class APIDownloader:

    def __init__(self, request_limit: int | None = None, rate_limit: RateLimit | None = None):
        self.request_count = 0
        self.limit = request_limit
        self.rate_limit = rate_limit

    def download(self, url, **kwargs):
        if self.limit is not None and self.request_count >= self.limit:
            raise RequestLimitExceeded(
                f"Request count reached or exceedem the limit {self.limit}: {self.request_count}"
            )
        response = requests.get(url, **kwargs)
        self.request_count += 1
        if self.rate_limit is not None:
            time.sleep(self.rate_limit.sleep)
        response.raise_for_status()
        return response
