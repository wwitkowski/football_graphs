import logging
import time
from collections import deque
from datetime import date, datetime, timezone
from enum import Enum
from typing import Generator, Literal

import requests
from sqlmodel import Session, func, select

from data_backend.exceptions import APIRequestException
from data_backend.models import Request, RequestStatus, RequestStatusEnum

logger = logging.getLogger(__name__)


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
        if self.rate_limit is not None:
            time.sleep(self.rate_limit.interval_seconds)

        logger.info(f"Making GET request to {url} with params {kwargs.get('params')}")
        try:
            response = self.http_session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise APIRequestException(f"Failed to download {url}: {e}") from e


class RequestTracker:
    """Tracks API request counts in the database."""

    def __init__(self, session: Session, request_limit: int | None = None):
        self.session = session
        self.limit = request_limit
        self.request_count = self._get_today_count() if request_limit is not None else 0

    def _get_today_count(self) -> int:
        today = date.today()
        stmt = (
            select(func.count(Request.id))
            .where(Request.updated_at >= today)
            .where(Request.status != RequestStatusEnum.PENDING)
        )
        return self.session.exec(stmt).one()

    def persist_requests(self, api_requests: list[Request]) -> None:
        """Persist requests in the DB in a single batch."""
        self.session.add_all(api_requests)
        self.session.commit()

    def get_pending_requests(self) -> list[Request]:
        """Get pending requests one by one."""
        stmt = select(Request).where(Request.status == RequestStatusEnum.PENDING)
        return self.session.exec(stmt).all()

    def complete_request(self, api_request: Request, status: RequestStatus) -> None:
        """Update the request status."""
        api_request.status = status
        api_request.updated_at = datetime.now(timezone.utc)
        self.session.commit()


class OnDownloadError(str, Enum):
    RAISE = "raise"
    CONTINUE = "continue"


OnDownloadErrorType = Literal[OnDownloadError.RAISE, OnDownloadError.CONTINUE]


class APIDownloader:
    """Coordinates HTTP requests with DB tracking."""

    def __init__(
        self,
        db_session: Session,
        http_session: requests.Session | None = None,
        request_limit: int | None = None,
        rate_limit: RateLimiter | None = None,
    ) -> None:
        self.tracker = RequestTracker(db_session, request_limit)
        self.requester = HTTPRequester(http_session, rate_limit)
        self._queue = deque(self.tracker.get_pending_requests())

    def add(self, requests: list[Request]) -> None:
        """Add new requests to the internal queue and persist them in DB."""
        self.tracker.persist_requests(requests)
        self._queue.extend(requests)

    def download_next(
        self, on_error: OnDownloadErrorType = "continue"
    ) -> Generator[requests.Response, None, None]:
        """Yield responses for requests in the internal queue, respecting limits."""
        while self._queue:
            request = self._queue.popleft()

            if (
                self.tracker.limit is not None
                and self.tracker.request_count >= self.tracker.limit
            ):
                logger.exception(f"Request limit of {self.tracker.limit} reached.")
                return

            try:
                logger.info(
                    f"Processing request: {request}, "
                    f"Request count: {self.tracker.request_count}, "
                    f"Queue size: {len(self._queue)}"
                )
                self.tracker.request_count += 1
                response = self.requester.get(
                    request.url, params=request.params, json=request.payload
                )
                self.tracker.complete_request(request, RequestStatusEnum.SUCCEEDED)
                yield request, response
            except APIRequestException as err:
                logger.exception(f"Request failed: {request}; Error: {err}")
                self.tracker.complete_request(request, RequestStatusEnum.FAILED)
                if on_error == OnDownloadError.RAISE:
                    raise
                elif on_error == OnDownloadError.CONTINUE:
                    continue
