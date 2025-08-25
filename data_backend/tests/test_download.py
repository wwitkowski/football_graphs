import pytest
from unittest import mock
from unittest.mock import MagicMock

import requests

from data_backend.download import HTTPRequester, RateLimit, RequestTracker
from data_backend.download import APIDownloader
from data_backend.exceptions import APIRequestException, RequestLimitExceeded
from data_backend.models import Request


@pytest.mark.parametrize(
    "limit,unit,expected_sleep_seconds",
    [(5, "seconds", 0.2), (30, "minutes", 2), (100, "hours", 36)],
)
def test_rate_limit_valid_units(limit, unit, expected_sleep_seconds):
    r = RateLimit(limit, unit)
    assert pytest.approx(r.sleep) == expected_sleep_seconds


def test_rate_limit_invalid_unit():
    with pytest.raises(ValueError, match="Invalid unit"):
        RateLimit(10, "days")


def test_http_requester_success():
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    session = MagicMock()
    session.get.return_value = mock_response

    requester = HTTPRequester(http_session=session)
    result = requester.get("http://example.com")

    assert result == mock_response
    session.get.assert_called_once_with("http://example.com")


@mock.patch("time.sleep", return_value=None)
def test_http_requester_rate_limit(mock_sleep):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    session = MagicMock()
    session.get.return_value = mock_response

    rate_limit = RateLimit(0.1, "seconds")
    requester = HTTPRequester(http_session=session, rate_limit=rate_limit)

    requester.get("http://example.com")
    mock_sleep.assert_called_once()


def test_http_requester_request_exception():
    session = MagicMock()
    session.get.side_effect = requests.exceptions.RequestException("boom")

    requester = HTTPRequester(http_session=session)

    with pytest.raises(APIRequestException):
        requester.get("http://example.com")


def test_http_requester_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")

    session = MagicMock()
    session.get.return_value = mock_response

    requester = HTTPRequester(http_session=session)

    with pytest.raises(APIRequestException):
        requester.get("http://example.com")


def test_request_tracker_begin_request():
    mock_session = MagicMock()

    tracker = RequestTracker(mock_session, service_name="svc")

    req1 = tracker.begin_request("http://example.com")
    assert req1.status == "Pending"
    assert tracker.request_count == 1
    mock_session.add.assert_called_once_with(req1)
    mock_session.commit.assert_called()


@mock.patch("data_backend.download.Request.get_today_count")
def test_request_tracker_begin_request_limit_exceeded(mock_get_count):
    mock_session = MagicMock()
    mock_get_count.return_value = 1

    tracker = RequestTracker(mock_session, request_limit=1, service_name="svc")

    with pytest.raises(RequestLimitExceeded):
        tracker.begin_request("http://example.com")


def test_request_tracker_complete_request():
    mock_session = MagicMock()
    tracker = RequestTracker(mock_session, service_name="svc")
    req = Request(url="x", request_count=0, created_by="svc", status="Pending")
    
    tracker.complete_request(req, status="Succeeded")
    assert req.status == "Succeeded"
    mock_session.commit.assert_called()


def test_apidownloader_download_success():
    mock_session = MagicMock()
    downloader = APIDownloader(mock_session, service_name="svc")

    mock_request = MagicMock()
    downloader.tracker.begin_request = MagicMock(return_value=mock_request)
    mock_response = MagicMock()
    downloader.requester.get = MagicMock(return_value=mock_response)
    downloader.tracker.complete_request = MagicMock()

    url = "http://example.com"
    response = downloader.download(url)

    assert response == mock_response
    downloader.tracker.begin_request.assert_called_once_with(url)
    downloader.requester.get.assert_called_once_with(url)
    downloader.tracker.complete_request.assert_called_once_with(mock_request, status="Succeeded")


def test_apidownloader_download_failure():
    mock_session = MagicMock()
    downloader = APIDownloader(mock_session, service_name="svc")

    mock_request = MagicMock()
    downloader.tracker.begin_request = MagicMock(return_value=mock_request)
    downloader.requester.get = MagicMock(side_effect=APIRequestException("boom"))
    downloader.tracker.complete_request = MagicMock()

    url = "http://example.com"
    with pytest.raises(APIRequestException):
        downloader.download(url)

    downloader.tracker.begin_request.assert_called_once_with(url)
    downloader.requester.get.assert_called_once_with(url)
    downloader.tracker.complete_request.assert_called_once_with(mock_request, status="Failed")
