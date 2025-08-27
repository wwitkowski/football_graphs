import time
from typing import Literal

import requests
from sqlmodel import Session

from data_backend.exceptions import APIRequestException, RequestLimitExceeded
from data_backend.models import Request, RequestStatus


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


class HTTPRequester:
    """Handles HTTP requests with optional rate limiting."""

    def __init__(
        self,
        http_session: requests.Session | None = None,
        rate_limit: RateLimiter | None = None,
    ):
        self.http_session = http_session or requests.Session()
        self.rate_limit = rate_limit

    def get(self, url: str, **kwargs) -> requests.Response:
        try:
            response = self.http_session.get(url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise APIRequestException(f"Failed to download {url}: {e}") from e

        if self.rate_limit is not None:
            time.sleep(self.rate_limit.interval_seconds)

        return response


class RequestTracker:
    """Tracks API request counts in the database."""

    def __init__(
        self, db_session: Session, service_name: str, request_limit: int | None = None
    ):
        self.session = db_session
        self.service_name = service_name
        self.limit = request_limit
        self.request_count = (
            Request.get_today_count(self.session) if request_limit is not None else 0
        )

    def begin_request(self, url: str) -> Request:
        """Claim a request slot and create a pending request record."""
        if self.limit is not None and self.request_count >= self.limit:
            raise RequestLimitExceeded(
                f"Request count exceeded the limit of "
                f"{self.limit}: {self.request_count}"
            )

        self.request_count += 1
        request = Request(
            url=url,
            created_by=self.service_name,
            status="Pending",
        )
        self.session.add(request)
        self.session.commit()
        return request

    def complete_request(self, request: Request, status: RequestStatus) -> None:
        """Update the request status."""
        request.status = status
        self.session.commit()


class APIDownloader:
    """Coordinates HTTP requests with DB tracking."""

    def __init__(
        self,
        db_session: Session,
        service_name: str,
        http_session: requests.Session | None = None,
        request_limit: int | None = None,
        rate_limit: RateLimiter | None = None,
    ) -> None:
        self.tracker = RequestTracker(db_session, service_name, request_limit)
        self.requester = HTTPRequester(http_session, rate_limit)

    def download(self, url: str, **kwargs) -> requests.Response:
        request = self.tracker.begin_request(url)
        try:
            response = self.requester.get(url, **kwargs)
            self.tracker.complete_request(request, status="Succeeded")
            return response
        except APIRequestException:
            self.tracker.complete_request(request, status="Failed")
            raise
