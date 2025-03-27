from data_backend.api import FootballAPIClient
from data_backend.download import APIDownloader
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_downloader():
    mock = MagicMock(spec=APIDownloader)
    return mock


@pytest.fixture
def football_api_client(mock_downloader):
    client = FootballAPIClient(api_key="test_api_key")
    client.downloader = mock_downloader
    return client


def test_fetch_success(football_api_client, mock_downloader):
    mock_response = MagicMock()
    mock_response.json.return_value = {"success": True, "data": []}
    mock_downloader.download.return_value = mock_response

    endpoint = "teams"
    params = {"league": "39", "season": "2021"}
    response = football_api_client.fetch(endpoint, params)

    mock_downloader.download.assert_called_once_with(
        "https://api-football-v1.p.rapidapi.com/v3/teams",
        headers={
            "x-rapidapi-key": "test_api_key",
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        },
        params=params,
    )
    assert response == {"success": True, "data": []}
