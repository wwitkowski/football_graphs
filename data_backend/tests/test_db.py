from unittest import mock
from unittest.mock import MagicMock

from data_backend.db import get_db_session, init_db


@mock.patch("data_backend.db.create_engine")
def test_init_db(mock_create_engine):
    db_url = "sqlite:///:memory:"
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    init_db(db_url)
    mock_create_engine.assert_called_once_with(db_url)


@mock.patch("data_backend.db.init_db")
def test_get_session_yields_and_closes(mock_init_db):
    mock_session = MagicMock()
    mock_init_db.return_value = mock_session

    with get_db_session("sqlite:///:memory:") as session:
        assert session == mock_session

    mock_session.close.assert_called_once()
