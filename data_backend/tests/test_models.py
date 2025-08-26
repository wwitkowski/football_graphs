from unittest.mock import MagicMock

from data_backend.models import Request


def test_request_creation():
    req = Request(url="http://example.com", created_by="svc")
    assert req.url == "http://example.com"
    assert req.status == "Pending"
    assert req.created_by == "svc"
    assert req.created_at is None


def test_request_get_today_count():
    mock_session = MagicMock()
    mock_session.exec.return_value.one.return_value = 1
    count = Request.get_today_count(mock_session)
    assert count == 1
    mock_session.exec.assert_called_once()
