from unittest.mock import MagicMock

from data_backend.models import Request


def test_request_creation():
    req = Request(url="http://example.com", created_by="svc")
    assert req.url == "http://example.com"
    assert req.status == "Pending"
    assert req.created_by == "svc"
    assert req.created_at is None
