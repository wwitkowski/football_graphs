import time
import requests
from typing import Literal
from sqlmodel import Session

from data_backend.exceptions import APIRequestException, RequestLimitExceeded
from data_backend.models import Request, RequestStatus


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
    

class HTTPRequester:
    """Handles HTTP requests with optional rate limiting."""

    def __init__(self, http_session: requests.Session | None = None, rate_limit: RateLimit | None = None):
        self.http_session = http_session or requests.Session()
        self.rate_limit = rate_limit

    def get(self, url: str, **kwargs) -> requests.Response:
        try:
            response = self.http_session.get(url, **kwargs)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise APIRequestException(f"Failed to download {url}: {e}") from e

        if self.rate_limit is not None:
            time.sleep(self.rate_limit.sleep)

        return response


class RequestTracker:
    """Tracks API request counts in the database."""

    def __init__(self, db_session: Session, service_name: str, request_limit: int | None = None):
        self.session = db_session
        self.limit = request_limit
        self.service_name = service_name
        self.request_count = Request.get_today_count(self.session) if request_limit is not None else 0

    def begin_request(self, url: str) -> Request:
        """Claim a request slot and create a pending request record."""
        if self.limit is not None and self.request_count >= self.limit:
            raise RequestLimitExceeded(f"Request count exceeded the limit of {self.limit}: {self.request_count}")
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
        *,
        service_name: str,
        http_session: requests.Session | None = None,
        request_limit: int | None = None,
        rate_limit: RateLimit | None = None,
    ) -> None:
        self.tracker = RequestTracker(db_session, request_limit, service_name)
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
