import logging
import time

import requests

from data_backend.exceptions import RequestLimitReachedException
from data_backend.models import APIRequest, APIResponse
from data_backend.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class HTTPRequester:
    """
    Handles HTTP GET requests with optional rate limiting and request limits.

    This class provides a convenient wrapper around ``requests.Session`` to enforce
    request limits (total number of requests) and rate limits (minimum delay between
    requests).
    """

    def __init__(
        self,
        http_session: requests.Session | None = None,
        rate_limit: RateLimiter | None = None,
        request_limit: int | None = None,
        request_count: int = 0,
    ) -> None:
        """
        Initialize an HTTPRequester.

        Parameters
        ----------
        http_session : requests.Session, optional
            A custom requests session to use for HTTP requests. If ``None``,
            a new session is created. Default is ``None``.
        rate_limit : RateLimiter, optional
            An optional rate limiter. If provided, a sleep interval is enforced
            before each request. Default is ``None``.
        request_limit : int, optional
            The maximum number of requests allowed. If ``None``, there is no limit.
            Default is ``None``.
        request_count : int, optional
            Initial request count (e.g., for resuming an interrupted run).
            Default is ``0``.
        """
        self.http_session: requests.Session = http_session or requests.Session()
        self.rate_limit: RateLimiter | None = rate_limit
        self.request_limit: int | None = request_limit
        self.request_count: int = request_count

    def get(self, request: APIRequest) -> APIResponse:
        """
        Perform an HTTP GET request with optional rate and request limits.

        Parameters
        ----------
        request : APIRequest
            The request object containing URL, parameters, and payload.

        Returns
        -------
        APIResponse
            The response object containing body, request, and error (if any).

        Raises
        ------
        RequestLimitReachedException
            If the request limit has been reached.
        """
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
