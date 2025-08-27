import os
from pathlib import Path
from unittest import mock

import pytest

from scripts.football_api.download_ongoing import (
    get_config,
    get_db_url,
    main,
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
def mock_api_client(
    mock_schedule_data, mock_fixture_stats_data, mock_player_stats_data
):
    client = mock.Mock()
    client.fetch.side_effect = [
        mock_schedule_data,
        mock_fixture_stats_data,
        mock_player_stats_data,
    ]
    return client


@pytest.fixture
def mock_s3_client():
    return mock.Mock()


@mock.patch.dict(
    "os.environ",
    {
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "host",
    },
    clear=True,
)
def test_get_db_url_success():
    expected = "postgresql+psycopg2://user:pass@host:5432/db"
    assert get_db_url() == expected


@mock.patch.dict(
    "os.environ",
    {"POSTGRES_USER": "user", "POSTGRES_PASSWORD": "pass", "POSTGRES_DB": "db"},
    clear=True,
)  # host not set → should default to localhost
def test_get_db_url_default_host():
    expected = "postgresql+psycopg2://user:pass@localhost:5432/db"
    assert get_db_url() == expected


@mock.patch.dict("os.environ", {}, clear=True)  # all env vars missing
def test_get_db_url_missing_env():
    with pytest.raises(EnvironmentError):
        get_db_url()


def test_get_config_success(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("leagues:\n  10: 'Friendlies'")

    result = get_config(config_path)
    assert isinstance(result, dict)
    assert result["leagues"][10] == "Friendlies"


def test_get_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        get_config(Path("nonexistent_config.yaml"))


def test_get_config_invalid_yaml(tmp_path):
    config_path = tmp_path / "bad_config.yaml"
    config_path.write_text("::: this is not yaml :::")

    with pytest.raises(RuntimeError):
        get_config(config_path)


@mock.patch.dict(
    os.environ,
    {
        "API_FOOTBALL_KEY": "dummy_key",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "pass",
        "POSTGRES_DB": "db",
        "POSTGRES_HOST": "localhost",
    },
)
def test_run_download_football_api(
    mock_api_client,
    mock_s3_client,
    mock_schedule_data,
    mock_fixture_stats_data,
    mock_player_stats_data,
):
    date = "2024-01-01"
    run_download_football_api(
        date, api_client=mock_api_client, s3_client=mock_s3_client
    )

    expected_api_calls = [
        mock.call("fixtures", {"date": date}),
        mock.call("fixtures/statistics", {"fixture": 1435553}),
        mock.call("fixtures/players", {"fixture": 1435553}),
    ]
    mock_api_client.fetch.assert_has_calls(expected_api_calls, any_order=False)

    expected_s3_calls = [
        mock.call.upload_json(mock_schedule_data, f"{date}/schedule.json"),
        mock.call.upload_json(
            mock_fixture_stats_data, f"{date}/1435553_fixture_statistics.json"
        ),
        mock.call.upload_json(
            mock_player_stats_data, f"{date}/1435553_player_statistics.json"
        ),
    ]
    mock_s3_client.assert_has_calls(expected_s3_calls, any_order=False)


@mock.patch(
    "scripts.football_api.download_ongoing.run_download_football_api", autospec=True
)
def test_main(mock_run_download_football_api):
    date = "2024-01-01"
    main([date])
    mock_run_download_football_api.assert_called_once_with(date)
