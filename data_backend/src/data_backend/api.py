import logging
from collections import deque
from typing import Deque

import requests

from data_backend.aws import S3Client
from data_backend.database.models import RequestStatusEnum
from data_backend.database.requests import RequestStore
from data_backend.exceptions import RequestLimitReachedException
from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest
from data_backend.rate_limiter import RateLimiter
from data_backend.requester import HTTPRequester

logger = logging.getLogger(__name__)


class APIDownloader:
    """
    Coordinates HTTP requests, persistence, and response handling.

    This class manages the lifecycle of API requests:
    - Persists requests in the database.
    - Executes them with rate/request limits.
    - Parses responses with a response handler.
    - Stores raw data in object storage.
    - Marks requests as succeeded or failed.
    """

    def __init__(
        self,
        name: str,
        response_handler: ResponseHandler,
        http_session: requests.Session | None = None,
        rate_limit: RateLimiter | None = None,
        request_limit: int | None = None,
        storage_client: S3Client = S3Client(
            bucket_name="raw-data", endpoint="http://minio:9000"
        ),
        request_store: RequestStore = RequestStore(),
    ) -> None:
        """
        Initialize an APIDownloader.

        Parameters
        ----------
        response_handler : ResponseHandler
            A handler responsible for parsing responses and generating new requests.
        http_session : requests.Session, optional
            A custom HTTP session for requests. If None, a new session is created.
        rate_limit : RateLimiter, optional
            An optional rate limiter to throttle request frequency.
        request_limit : int, optional
            Maximum number of requests allowed in this session. If None, unlimited.
        storage_client : S3Client, optional
            Object storage client for persisting raw responses. Default stores in MinIO.
        request_store : RequestStore, optional
            Database access object for persisting and retrieving requests.
        """
        self.name = name
        self.requests: RequestStore = request_store
        self.handler: ResponseHandler = response_handler
        self.files: S3Client = storage_client
        self.requester: HTTPRequester = HTTPRequester(
            http_session=http_session,
            rate_limit=rate_limit,
            request_limit=request_limit,
            request_count=self.requests.get_today_count(name=name),
        )
        self._queue: Deque[APIRequest] = deque()

    def _add(self, requests: list[APIRequest]) -> None:
        """
        Add requests to the processing queue and persist them in the database.

        Parameters
        ----------
        requests : list of APIRequest
            The requests to enqueue and persist.
        """
        self._queue.extend(requests)
        self.requests.add(requests, self.name)

    def _download(self) -> None:
        """
        Process requests in the queue until it is empty.
        """
        while self._queue:
            request = self._queue.popleft()

            try:
                response = self.requester.get(request)
            except RequestLimitReachedException:
                logger.exception(
                    f"Request limit of {self.requester.request_limit} reached."
                )
                return

            print(f"DEBUG Response: {response}")

            if response.error:
                logger.exception(f"Error downloading {request.url}: {response.error}")
                self.requests.complete(request, RequestStatusEnum.FAILED)
                continue

            data, path = self.handler.handle(response)
            self.files.save_json(data, path)
            new_requests = list(self.handler.collect_new_requests())
            self._add(new_requests)
            req_status = RequestStatusEnum.SUCCEEDED
            self.requests.complete(request, req_status)

    def download(self, request: APIRequest) -> None:
        """
        Add a single request to the queue and start download process.

        Parameters
        ----------
        request : APIRequest
            The request to process.
        """
        self._add([request])
        self._download()

    def download_backlog(self) -> None:
        """
        Download all pending requests from the database.
        """
        pending_requests = self.requests.get_pending(self.name)
        logger.info(f"Found {len(pending_requests)} pending requests to download.")
        self._queue.extend(pending_requests)
        self._download()
