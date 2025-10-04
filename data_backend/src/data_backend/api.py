import logging
from collections import deque

from data_backend.aws import S3Client
from data_backend.database.requests import RequestStore
from data_backend.exceptions import RequestLimitReachedException
from data_backend.database.models import RequestStatusEnum
from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest
from data_backend.requester import HTTPRequester


logger = logging.getLogger(__name__)


class APIDownloader:
    """Coordinates HTTP requests with DB tracking."""

    def __init__(
        self,
        response_handler: ResponseHandler,
        request_store: RequestStore,
        storage_client: S3Client,
        requester: HTTPRequester,
    ) -> None:
        self.requests = request_store
        self.handler = response_handler
        self.files = storage_client
        self.requester = requester
        self._queue = deque()

    def _add(self, requests: list[APIRequest]) -> None:
        self._queue.extend(requests)
        self.requests.add(requests)

    def download(self, request: APIRequest) -> None:
        self._add([request])

        while self._queue:
            request = self._queue.popleft()

            try:
                response = self.requester.get(request)
            except RequestLimitReachedException:
                logger.exception(f"Request limit of {self.requester.request_limit} reached.")
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
