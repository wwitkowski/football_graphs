import os
from unittest import mock

import pytest
from data_backend.models import Request
from freezegun import freeze_time

from scripts.football_api.football_api import (
    BASE_URL,
    handle_schedule_response,
    handle_stats_response,
    run_download_football_api,
)


@pytest.fixture
def mock_schedule_data():
    return {
        "get": "fixtures",
        "parameters": {"date": "2021-01-29"},
        "errors": [],
        "results": 108,
        "paging": {"current": 1, "total": 1},
        "response": [
            {
                "fixture": {
                    "id": 1435553,
                    "timezone": "UTC",
                    "date": "2025-08-27T16:45:00+00:00",
                    "status": {
                        "short": "NS",
                    },
                },
                "league": {
                    "id": 2,
                    "name": "UEFA Champions League",
                    "country": "World",
                },
                "teams": {
                    "home": {
                        "id": 556,
                        "name": "Qarabag",
                    },
                    "away": {
                        "id": 651,
                        "name": "Ferencvarosi TC",
                    },
                },
                "goals": {"home": None, "away": None},
            },
            {
                "fixture": {
                    "id": 663685,
                    "timezone": "UTC",
                    "date": "2021-01-29T00:00:00+00:00",
                    "status": {"short": "FT"},
                },
                "league": {"id": 10, "name": "Friendlies", "country": "World"},
                "teams": {
                    "home": {"id": 11, "name": "Panama"},
                    "away": {"id": 14, "name": "Serbia"},
                },
                "goals": {"home": 0, "away": 0},
            },
        ],
    }


@pytest.fixture
def mock_fixture_stats_data():
    return {
        "errors": [],
        "get": "api/v3/fixtures/statistics",
        "paging": {"current": 1, "total": 1},
        "parameters": {"fixture": "215662"},
        "response": [
            {
                "statistics": [
                    {"type": "Shots on Goal", "value": 3},
                    {"type": "Shots off Goal", "value": 2},
                ],
                "team": {"id": 463, "name": "Aldosivi"},
            },
            {
                "statistics": [
                    {"type": "Shots on Goal", "value": None},
                    {"type": "Shots off Goal", "value": 3},
                ],
                "team": {"id": 442, "name": "Defensa Y Justicia"},
            },
        ],
        "results": 2,
    }


@pytest.fixture
def mock_player_stats_data():
    return {
        "get": "fixtures/players",
        "parameters": {"fixture": "169080"},
        "errors": [],
        "results": 2,
        "paging": {"current": 1, "total": 1},
        "response": [
            {
                "team": {"id": 2284, "name": "Monarcas"},
                "players": [
                    {
                        "player": {"id": 35931, "name": "Sebastián Sosa"},
                        "statistics": [
                            {
                                "games": {
                                    "minutes": 90,
                                    "position": "G",
                                    "rating": "6.3",
                                    "captain": False,
                                },
                                "shots": {"total": 0, "on": 0},
                            }
                        ],
                    }
                ],
            },
            {
                "team": {"id": 2283, "name": "Atlas"},
                "players": [
                    {
                        "player": {"id": 2482, "name": "Camilo Vargas"},
                        "statistics": [
                            {
                                "games": {
                                    "minutes": 90,
                                    "position": "G",
                                    "rating": "8.6",
                                    "captain": False,
                                },
                                "shots": {"total": 0, "on": 0},
                            }
                        ],
                    }
                ],
            },
        ],
    }


@pytest.fixture
def mock_s3():
    return mock.Mock()


@freeze_time("2025-01-01")
def test_handle_schedule_response(mock_s3, mock_schedule_data):
    new_requests = handle_schedule_response(
        mock_schedule_data,
        date="2025-01-01",
        league_ids=[2],
        s3_client=mock_s3,
    )
    expected_requests = [
        Request(
            endpoint=f"{BASE_URL}/fixtures/statistics",
            params={"fixture": 1435553},
            request_metadata={"date": "2025-01-01"},
        ),
        Request(
            endpoint=f"{BASE_URL}/fixtures/players",
            params={"fixture": 1435553},
            request_metadata={"date": "2025-01-01"},
        ),
    ]
    mock_s3.upload_json.assert_called_once_with(
        mock_schedule_data, "2025-01-01/schedule.json"
    )
    assert new_requests == expected_requests


def test_handle_schedule_response_no_leagues(mock_s3, mock_schedule_data):
    new_requests = handle_schedule_response(
        mock_schedule_data,
        date="2025-01-01",
        league_ids=[120],
        s3_client=mock_s3,
    )
    mock_s3.upload_json.assert_called_once_with(
        mock_schedule_data, "2025-01-01/schedule.json"
    )
    assert new_requests == []


def test_handle_stats_response_stats(mock_s3, mock_fixture_stats_data):
    handle_stats_response(mock_fixture_stats_data, "2025-01-01", s3_client=mock_s3)
    mock_s3.upload_json.assert_called_once_with(
        mock_fixture_stats_data, "2025-01-01/215662_statistics.json"
    )


def test_handle_stats_response_players(mock_s3, mock_player_stats_data):
    handle_stats_response(mock_player_stats_data, "2025-01-01", s3_client=mock_s3)
    mock_s3.upload_json.assert_called_once_with(
        mock_player_stats_data, "2025-01-01/169080_players.json"
    )


@mock.patch.dict(os.environ, {"API_FOOTBALL_KEY": "fake_key"})
@mock.patch("scripts.football_api.football_api.S3Client", autospec=True)
@mock.patch("scripts.football_api.football_api.APIDownloader", autospec=True)
@mock.patch("scripts.football_api.football_api.get_db_session")
@mock.patch("scripts.football_api.football_api.get_db_url")
@mock.patch("scripts.football_api.football_api.get_config")
@mock.patch("scripts.football_api.football_api.handle_schedule_response")
@mock.patch("scripts.football_api.football_api.handle_stats_response")
def test_run_download_football_api(
    mock_handle_stats,
    mock_handle_schedule,
    mock_get_config,
    mock_get_db_url,
    mock_get_db_session,
    mock_api_downloader_cls,
    mock_s3_client,
    mock_schedule_data,
    mock_fixture_stats_data,
    mock_player_stats_data,
):
    mock_get_db_url.return_value = "sqlite://"
    mock_db_session = mock.Mock()
    mock_get_db_session.return_value.__enter__.return_value = mock_db_session
    mock_get_config.return_value = {"leagues": [2, 39]}

    mock_requests = [
        Request(
            endpoint=f"{BASE_URL}/fixtures",
            params={"date": "2025-01-01"},
            request_metadata={"date": "2025-01-01"},
        ),
        Request(
            endpoint=f"{BASE_URL}/fixtures/statistics",
            params={"fixture": 1435553},
            request_metadata={"date": "2025-01-01"},
        ),
        Request(
            endpoint=f"{BASE_URL}/fixtures/players",
            params={"fixture": 1435553},
            request_metadata={"date": "2025-01-01"},
        ),
    ]

    mock_downloader = mock.Mock()
    mock_api_downloader_cls.return_value = mock_downloader
    mock_downloader.download_next.return_value = [
        (mock_requests[0], mock.Mock(json=mock.Mock(return_value=mock_schedule_data))),
        (
            mock_requests[1],
            mock.Mock(json=mock.Mock(return_value=mock_fixture_stats_data)),
        ),
        (
            mock_requests[2],
            mock.Mock(json=mock.Mock(return_value=mock_player_stats_data)),
        ),
    ]
    mock_handle_schedule.return_value = mock_requests[1:]

    run_download_football_api("2025-01-01")

    mock_get_db_url.assert_called_once()
    mock_get_db_session.assert_called_once_with("sqlite://")
    mock_downloader.add.has_calls = [
        mock.call([mock_requests[0]]),
        mock.call([mock_requests[1:]]),
    ]
    mock_handle_schedule.assert_called_once_with(
        mock_schedule_data, "2025-01-01", [2, 39], mock_s3_client.return_value
    )
    mock_handle_stats.has_calls = [
        mock.call(mock_fixture_stats_data, "2025-01-01", mock_s3_client.return_value),
        mock.call(mock_player_stats_data, "2025-01-01", mock_s3_client.return_value),
    ]
