import logging
import time

from data_backend.models import APIRequest, APIResponse
from data_backend.rate_limiter import RateLimiter
import requests

from data_backend.exceptions import RequestLimitReachedException


logger = logging.getLogger(__name__)


class HTTPRequester:
    """Handles HTTP requests with optional rate limiting."""

    def __init__(
        self,
        http_session: requests.Session | None = None,
        rate_limit: RateLimiter | None = None,
        request_limit: int | None = None,
        request_count: int = 0,
    ):
        self.http_session = http_session or requests.Session()
        self.rate_limit = rate_limit
        self.request_limit = request_limit
        self.request_count = request_count

    def get(self, request: APIRequest) -> APIResponse:
        if self.request_limit is not None and self.request_count >= self.request_limit:
            raise RequestLimitReachedException(
                f"Request limit of {self.request_limit} reached."
            )

        if self.rate_limit is not None:
            time.sleep(self.rate_limit.interval_seconds)

        logger.info(f"Making GET request to {request.url}")
        self.request_count += 1
        try:
            response = self.http_session.get(
                request.url, params=request.params, json=request.payload
            )
            response.raise_for_status()
            return APIResponse(
                body=response.text,
                request=request,
                error=None,
            )

        except requests.exceptions.HTTPError as e:
            response_body = e.response.text if e.response else ""
            error_msg = str(e)
            logger.error(
                f"HTTP error for {request.url}: {error_msg}\nBody: {response_body}"
            )
            return APIResponse(
                body=response_body,
                request=request,
                error=error_msg,
            )

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            logger.error(f"Request failed for {request.url}: {error_msg}")
            return APIResponse(
                body="",
                request=request,
                error=error_msg,
            )
