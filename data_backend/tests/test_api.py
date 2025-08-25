from unittest.mock import MagicMock

from data_backend.api import FootballAPIClient, get_db_session


def test_client_initialization():
    client = FootballAPIClient(api_key="test-key", db_url="sqlite:///:memory:")
    assert client.headers["x-rapidapi-key"] == "test-key"
    assert client.headers["x-rapidapi-host"] == "api-football-v1.p.rapidapi.com"
    assert client.request_limit == 100
    assert client.http_session.headers["x-rapidapi-key"] == "test-key"


def test_get_session_yields_and_closes():
    mock_session = MagicMock()

    def fake_factory(db_url):
        return mock_session

    with get_db_session("sqlite:///:memory:", fake_factory) as session:
        assert session == mock_session

    mock_session.close.assert_called_once()


def test_fetch_success():
    mock_session = MagicMock()
    mock_downloader = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "ok"}
    mock_downloader.download.return_value = mock_response

    client = FootballAPIClient(
        api_key="test-key", 
        db_url="sqlite:///:memory:", 
        session_factory=lambda db_url: mock_session, 
        downloader_cls=lambda *a, **kw: mock_downloader
    )

    result = client.fetch("fixtures", {"league": "EPL"})

    assert result == {"data": "ok"}
    mock_downloader.download.assert_called_once_with(
        "https://api-football-v1.p.rapidapi.com/v3/fixtures",
        params={"league": "EPL"},
    )
