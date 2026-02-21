import pytest
import json

from data_backend.api import APIDownloader
from scripts.football_api import football_api


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


def test_parse_schedule_response_success(mock_schedule_data):
    data, filename = football_api.parse_schedule_response(json.dumps(mock_schedule_data))
    assert data == mock_schedule_data
    assert filename == "2021-01-29_schedule.json"


def test_parse_schedule_response_missing_date_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        data, filename = football_api.parse_schedule_response(
            json.dumps({"parameters": {}, "response": []})
        )
    assert data["response"] == []
    assert filename == "_schedule.json"
    assert "missing 'date' parameter" in caplog.text


def test_generate_fixture_requests_filters_by_league(mock_schedule_data):
    requests = football_api.generate_fixture_requests(
        json.dumps(mock_schedule_data), league_ids=["2", "3"]
    )
    assert len(requests) == 2
    assert requests[0].type == "match_stats"
    assert requests[0].url.endswith("/fixtures/statistics")
    assert requests[0].params == {"fixture": "1435553"}
    assert requests[1].type == "player_stats"
    assert requests[1].url.endswith("/fixtures/players")
    assert requests[1].params == {"fixture": "1435553"}


def test_parse_stats_response_for_match_stats(mock_fixture_stats_data):
    data, filename = football_api.parse_stats_response(json.dumps(mock_fixture_stats_data))
    assert data == mock_fixture_stats_data
    assert filename == "215662_statistics.json"


def test_parse_stats_response_for_player_stats(mock_player_stats_data):
    data, filename = football_api.parse_stats_response(json.dumps(mock_player_stats_data))
    assert data == mock_player_stats_data
    assert filename == "169080_players.json"


def test_parse_stats_response_missing_fields_logs_warning(caplog):
    with caplog.at_level("WARNING"):
        _, filename = football_api.parse_stats_response(json.dumps({"parameters": {}}))
    assert filename == "None_.json"
    assert "missing 'fixture' parameter or 'get' field" in caplog.text


def test_get_football_api_downloader_builds_components():
    class FakeSession:
        def __init__(self):
            self.headers = {}

    class FakeRequestStore:
        def get_today_count(self, name):
            return 0

    class FakeStorageClient:
        pass

    fake_session = FakeSession()
    fake_request_store = FakeRequestStore()
    fake_storage_client = FakeStorageClient()

    downloader = football_api.get_football_api_downloader(
        name="daily-job",
        http_session=fake_session,
        config={"leagues": [2, 3]},
        request_store=fake_request_store,
        storage_client=fake_storage_client,
    )

    assert isinstance(downloader, APIDownloader)
    assert downloader.name == "daily-job"
    assert downloader.requests is fake_request_store
    assert downloader.files is fake_storage_client
    assert downloader.requester.http_session is fake_session
    assert downloader.requester.request_limit == football_api.REQUEST_DAILY_LIMIT
    assert fake_session.headers["x-rapidapi-host"] == football_api.API_HOST
    assert "x-rapidapi-key" in fake_session.headers

    handler = downloader.handler
    assert set(handler.parsers) == {"schedule", "match_stats", "player_stats"}
    assert "schedule" in handler.generators
    assert len(handler.generators["schedule"]) == 1


def test_start_download_downloads_backlog_then_schedule_request():
    class FakeDownloader:
        def __init__(self):
            self.calls = []

        def download_backlog(self):
            self.calls.append("backlog")

        def download(self, request):
            self.calls.append(("download", request))

    downloader = FakeDownloader()
    football_api.start_download(downloader, "2026-02-20")

    assert downloader.calls[0] == "backlog"
    _, schedule_request = downloader.calls[1]
    assert schedule_request.type == "schedule"
    assert schedule_request.url.endswith("/fixtures")
    assert schedule_request.params == {"date": "2026-02-20"}
