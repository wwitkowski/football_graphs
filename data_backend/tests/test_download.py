import pytest
from unittest import mock
import time

import requests

from data_backend.download import RateLimit
from data_backend.download import APIDownloader
from data_backend.exceptions import APIRequestException, APIRequestLimitExceeded


@pytest.fixture
def mock_requests_get():
    with mock.patch("requests.get") as mock_get:
        yield mock_get


@pytest.mark.parametrize(
    "limit,unit,expected_sleep_seconds",
    [(5, "seconds", 0.2), (30, "minutes", 2), (100, "hours", 36)],
)
def test_rate_limit_init_valid_unit(limit, unit, expected_sleep_seconds):
    rate_limit = RateLimit(limit=limit, unit=unit)
    assert rate_limit.sleep == expected_sleep_seconds


def test_rate_limit_invalid_unit():
    with pytest.raises(
        ValueError, match="Invalid unit: invalid_unit. Should be one of:"
    ):
        RateLimit(limit=5, unit="invalid_unit")


def test_apidownloader_download(mock_requests_get):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.text = "data"
    downloader = APIDownloader()
    resp = downloader.download("https://example.com")

    assert resp.status_code == 200
    assert resp.text == "data"


def test_apidownloader_request_exception(mock_requests_get):
    mock_requests_get.side_effect = requests.exceptions.RequestException()
    downloader = APIDownloader()
    with pytest.raises(APIRequestException):
        downloader.download("https://example.com")


def test_apidownloader_http_error(mock_requests_get):
    mock_response = mock.MagicMock(spec=requests.Response)
    mock_response.status_code = 500

    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_requests_get.return_value = mock_response

    downloader = APIDownloader()
    with pytest.raises(APIRequestException):
        downloader.download("https://example.com")


def test_apidownloader_request_limit(mock_requests_get):
    mock_requests_get.return_value.status_code = 200
    downloader = APIDownloader(request_limit=3)
    downloader.download("https://example.com")
    downloader.download("https://example.com")
    downloader.download("https://example.com")

    with pytest.raises(APIRequestLimitExceeded):
        downloader.download("https://example.com")


@pytest.mark.parametrize("request_count_limit", [5, 10, 15])
def test_apidownloader_rate_limit(request_count_limit, mock_requests_get):
    rate_limit = RateLimit(
        limit=request_count_limit, unit="seconds"
    )  # Sleep for 2 seconds
    downloader = APIDownloader(rate_limit=rate_limit)

    start_time = time.time()
    while time.time() - start_time < 1:
        downloader.download("https://example.com")

    assert downloader.request_count == request_count_limit
