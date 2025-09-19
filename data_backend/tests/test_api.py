from datetime import datetime, timezone
from unittest import mock
from unittest.mock import MagicMock

import pytest
import requests
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from data_backend.api import (
    APIDownloader,
    HTTPRequester,
    RateLimiter,
    RequestTracker,
)
from data_backend.exceptions import APIRequestException
from data_backend.models import Request


@pytest.fixture(scope="function")
def session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    SQLModel.metadata.drop_all(engine)


@pytest.mark.parametrize(
    "events_per_unit,unit,expected_interval_seconds",
    [(5, "second", 0.2), (30, "minute", 2), (100, "hour", 36)],
)
def test_rate_limit_valid_units(events_per_unit, unit, expected_interval_seconds):
    r = RateLimiter(events_per_unit, unit)
    assert pytest.approx(r.interval_seconds) == expected_interval_seconds


def test_rate_limit_invalid_unit():
    with pytest.raises(ValueError, match="Invalid unit"):
        RateLimiter(10, "days")


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

    rate_limit = RateLimiter(0.1, "second")
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
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "HTTP Error"
    )

    session = MagicMock()
    session.get.return_value = mock_response

    requester = HTTPRequester(http_session=session)

    with pytest.raises(APIRequestException):
        requester.get("http://example.com")


def test_request_tracker_init(session):
    session.add_all(
        [
            Request(url="http://example.com/1", status="Pending"),
            Request(url="http://example.com/2", status="Succeeded"),
            Request(
                url="http://example.com/old",
                updated_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
                status="Succeeded",
            ),
        ]
    )
    session.commit()
    tracker = RequestTracker(session, request_limit=10)
    assert tracker.session == session
    assert tracker.limit == 10
    assert tracker.request_count == 1


def test_request_tracker_persist_request(session):
    tracker = RequestTracker(session)
    requests = [
        Request(
            url="http://example.com",
        ),
        Request(
            url="http://example.org",
            params={"q": "test"},
        ),
    ]
    tracker.persist_requests(requests)
    added_requests = session.exec(select(Request)).all()
    assert requests == added_requests


def test_request_tracker_get_pending_requests(session):
    requests = [
        Request(
            url="http://example.com/1",
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status="Pending",
        ),
        Request(
            url="http://example.com/2",
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status="Succeeded",
        ),
    ]
    session.add_all(requests)
    session.commit()
    tracker = RequestTracker(session)
    pending_requests = tracker.get_pending_requests()
    assert len(pending_requests) == 1
    assert pending_requests[0] == requests[0]


@freeze_time("2025-01-02 12:00:00")
def test_request_tracker_complete_request(session):
    requests = [
        Request(
            url="http://example.com/1",
            updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            status="Pending",
        )
    ]
    session.add_all(requests)
    session.commit()
    tracker = RequestTracker(session)
    req = session.exec(select(Request)).one()
    tracker.complete_request(req, status="Succeeded")

    updated_req = session.exec(select(Request).where(Request.id == req.id)).one()
    assert updated_req.status == "Succeeded"
    assert updated_req.updated_at == datetime(2025, 1, 2, 12, 0)


def test_apidownloader_init(session):
    mock_http_session = MagicMock()

    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
        request_limit=10,
        rate_limit=RateLimiter(5, "second"),
    )
    assert isinstance(downloader.tracker, RequestTracker)
    assert isinstance(downloader.requester, HTTPRequester)
    assert downloader.tracker.session == session
    assert downloader.tracker.limit == 10
    assert downloader.tracker.request_count == 0
    assert downloader.requester.http_session == mock_http_session
    assert downloader.requester.rate_limit.events_per_unit == 5
    assert downloader.requester.rate_limit.unit == "second"


def test_apidownloader_add(session):
    mock_http_session = MagicMock()
    downloader = APIDownloader(session, http_session=mock_http_session)
    req = Request(url="http://example.com")
    downloader.add([req])
    added_req = session.exec(select(Request).where(Request.id == req.id)).one()
    assert added_req == req
    assert req in downloader._queue


def test_apidownloader_download_next(session):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    mock_http_session = MagicMock()
    mock_http_session.get.return_value = mock_response

    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
    )

    req1 = Request(url="http://example.com/1")
    req2 = Request(url="http://example.com/2")
    downloader.add([req1, req2])

    returned_objects = list(downloader.download_next())
    assert len(returned_objects) == 2
    assert returned_objects[0][0] == req1
    assert returned_objects[0][1] == mock_response
    assert returned_objects[1][0] == req2
    assert returned_objects[1][1] == mock_response


def test_apidownloader_request_limit_exceeded(session):
    mock_http_session = MagicMock()
    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
        request_limit=1,
    )

    req1 = Request(url="http://example.com/1")
    req2 = Request(url="http://example.com/2")
    downloader.add([req1, req2])

    assert len(list(downloader.download_next())) == 1


def test_apidownloader_raise_on_error(session):
    mock_http_session = MagicMock()
    mock_http_session.get.side_effect = requests.exceptions.RequestException()

    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
    )

    req = Request(url="http://example.com")
    downloader.add([req])

    with pytest.raises(APIRequestException):
        list(downloader.download_next(on_error="raise"))

    updated_req = session.exec(select(Request).where(Request.id == req.id)).one()
    assert updated_req.status == "Failed"


def test_apidownloader_continue_on_error(session):
    mock_http_session = MagicMock()
    mock_http_session.get.side_effect = requests.exceptions.RequestException()

    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
    )

    req1 = Request(url="http://example.com/1")
    req2 = Request(url="http://example.com/2")
    downloader.add([req1, req2])

    results = list(downloader.download_next(on_error="continue"))
    assert results == []

    updated_req1 = session.exec(select(Request).where(Request.id == req1.id)).one()
    updated_req2 = session.exec(select(Request).where(Request.id == req2.id)).one()
    assert updated_req1.status == "Failed"
    assert updated_req2.status == "Failed"


def test_apidownloader_request_count_w_exceptions(session):
    mock_http_session = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = [
        None,
        requests.exceptions.RequestException(),
        None,
    ]
    mock_http_session.get.return_value = mock_response

    downloader = APIDownloader(
        session,
        http_session=mock_http_session,
        request_limit=3,
    )

    req1 = Request(url="http://example.com/1")
    req2 = Request(url="http://example.com/2")
    req3 = Request(url="http://example.com/3")
    downloader.add([req1, req2, req3])

    list(downloader.download_next(on_error="continue"))

    assert downloader.tracker.request_count == 3
