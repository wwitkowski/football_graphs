from unittest import mock
from unittest.mock import MagicMock

from scripts.football_api.football_api import FootballAPIClient


def test_client_initialization():
    client = FootballAPIClient(api_key="test-key", db_url="sqlite:///:memory:")
    assert client.headers["x-rapidapi-key"] == "test-key"
    assert client.headers["x-rapidapi-host"] == "api-football-v1.p.rapidapi.com"
    assert client.request_limit == 100
    assert client.http_session.headers["x-rapidapi-key"] == "test-key"


@mock.patch("data_backend.api.get_db_session")
def test_fetch_success(mock_get_db_session):
    mock_session = MagicMock()
    mock_get_db_session.return_value.__enter__.return_value = mock_session
    mock_downloader = MagicMock()
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": "ok"}
    mock_downloader.download.return_value = mock_response

    client = FootballAPIClient(
        api_key="test-key",
        db_url="sqlite:///:memory:",
        downloader_cls=lambda *a, **kw: mock_downloader,
    )

    result = client.fetch("fixtures", {"league": "EPL"})

    assert result == {"data": "ok"}
    mock_downloader.download.assert_called_once_with(
        "https://api-football-v1.p.rapidapi.com/v3/fixtures",
        params={"league": "EPL"},
    )
