from unittest import mock
from data_backend.exceptions import RequestLimitReachedException
from data_backend.models import APIRequest, APIResponse
from data_backend.rate_limiter import RateLimiter
from data_backend.requester import HTTPRequester
import pytest
import requests

from tests.conftest import FakeHTTPSession, FakeResponse


def test_get_success():
    response = FakeResponse(text="ok", status_code=200)
    session = FakeHTTPSession(response=response)

    requester = HTTPRequester(http_session=session)
    req = APIRequest(url="http://test.com")
    result = requester.get(req)

    assert result == APIResponse(
        body="ok",
        request=req,
    )
    assert requester.request_count == 1


@mock.patch("time.sleep", return_value=None)
def test_get_rate_limit(mock_sleep):
    response = FakeResponse(text="ok", status_code=200)
    session = FakeHTTPSession(response=response)

    rate_limit = RateLimiter(0.1, "second")
    requester = HTTPRequester(http_session=session, rate_limit=rate_limit)

    req = APIRequest(url="http://test.com")
    requester.get(req)
    mock_sleep.assert_called_once()


def test_get_http_error():
    session = FakeHTTPSession(FakeResponse("Not Found", 404))
    requester = HTTPRequester(http_session=session)

    req = APIRequest(url="http://test.com")
    result = requester.get(req)

    assert result.body == "Not Found"
    assert result.error == "HTTP Error"


def test_request_exception():
    class BrokenHTTPSession:
        def get(self, *args, **kwargs):
            raise requests.exceptions.RequestException("Boom!")

    requester = HTTPRequester(http_session=BrokenHTTPSession())

    req = APIRequest(url="http://test.com")
    result = requester.get(req)

    assert result.error == "Boom!"
    assert result.body == ""


def test_get_request_limit_reached():
    requester = HTTPRequester(request_limit=1, request_count=1)

    with pytest.raises(RequestLimitReachedException):
        req = APIRequest(url="http://test.com")
        requester.get(req)
