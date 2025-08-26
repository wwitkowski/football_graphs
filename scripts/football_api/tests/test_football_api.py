from unittest import mock

import pytest

from scripts.football_api.football_api import main, run_download_football_api


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
                    "id": 663684,
                    "timezone": "UTC",
                    "date": "2021-01-29T00:00:00+00:00",
                    "status": {
                        "short": "FT",
                    },
                },
                "league": {
                    "id": 10,
                    "name": "Friendlies",
                    "country": "World",
                },
                "teams": {
                    "home": {
                        "id": 11,
                        "name": "Panama",
                    },
                    "away": {
                        "id": 14,
                        "name": "Serbia",
                    },
                },
                "goals": {"home": 0, "away": 0},
            }
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
                "team": {
                    "id": 2284,
                    "name": "Monarcas",
                },
                "players": [
                    {
                        "player": {
                            "id": 35931,
                            "name": "Sebastián Sosa",
                        },
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
                    },
                ],
            },
            {
                "team": {
                    "id": 2283,
                    "name": "Atlas",
                },
                "players": [
                    {
                        "player": {
                            "id": 2482,
                            "name": "Camilo Vargas",
                        },
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


@mock.patch("data_backend.aws.S3Client.upload_json")
@mock.patch("data_backend.api.FootballAPIClient.fetch")
def test_run_download_football_api(
    mock_api_fetch,
    mock_s3_upload_json,
    mock_schedule_data,
    mock_fixture_stats_data,
    mock_player_stats_data,
):
    mock_api_fetch.side_effect = [
        mock_schedule_data,
        mock_fixture_stats_data,
        mock_player_stats_data,
    ]

    date = "2024-01-01"
    run_download_football_api(date)

    expected_args_list = [
        ("fixtures", {"date": "2024-01-01"}),
        ("fixtures/statistics", {"fixture": 663684}),
        ("fixtures/players", {"fixture": 663684}),
    ]
    for args, expected_args in zip(mock_api_fetch.call_args_list, expected_args_list):
        assert args.args == expected_args

    expected_args_list = [
        (mock_schedule_data, f"{date}/schedule.json"),
        (mock_fixture_stats_data, f"{date}/663684_fixture_statistics.json"),
        (mock_player_stats_data, f"{date}/663684_player_statistics.json"),
    ]
    for args, expected_args in zip(
        mock_s3_upload_json.call_args_list, expected_args_list
    ):
        assert args.args == expected_args


@mock.patch("scripts.football_api.football_api.run_download_football_api")
def test_main(mock_run_download_football_api):
    date = "2024-01-01"
    main([date])
    mock_run_download_football_api.assert_called_once_with(date)
