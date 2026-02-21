import json
import logging
import os
from functools import partial
from pathlib import Path
from typing import Any

import requests
from data_backend.api import APIDownloader
from data_backend.config import get_config
from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_KEY = os.environ.get("API_FOOTBALL_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"
REQUEST_DAILY_LIMIT = 100

logger = logging.getLogger(__name__)


def parse_schedule_response(body: str) -> tuple[dict[str, Any], str]:
    """Parse schedule response, return data and date."""
    data = json.loads(body)
    date = data.get("parameters", {}).get("date", "")
    if not date:
        logger.warning("Schedule response missing 'date' parameter")
    return data, f"{date}_schedule.json"


def generate_fixture_requests(body: str, league_ids: list[str]) -> list[APIRequest]:
    """Generate fixture statistics and player requests from schedule response."""
    data = json.loads(body)
    requests = []
    for fixture in data.get("response", []):
        league_id = fixture.get("league", {}).get("id")
        fixture_id = fixture.get("fixture", {}).get("id")
        if not fixture_id or str(league_id) not in league_ids:
            continue
        requests.extend(
            [
                APIRequest(
                    url=f"{BASE_URL}/fixtures/statistics",
                    params={"fixture": fixture_id},
                    type="match_stats",
                ),
                APIRequest(
                    url=f"{BASE_URL}/fixtures/players",
                    params={"fixture": fixture_id},
                    type="player_stats",
                ),
            ]
        )
    return requests


def parse_stats_response(
    body: str,
) -> tuple[dict[str, Any], str]:
    data = json.loads(body)
    fixture_id = data.get("parameters", {}).get("fixture")
    endpoint = data.get("get", "")
    if not fixture_id or not endpoint:
        logger.warning("Stats response missing 'fixture' parameter or 'get' field")
    filename = endpoint.split("/")[-1]
    return data, f"{fixture_id}_{filename}.json"


def get_football_api_downloader(
    name: str,
    http_session: requests.Session | None = None,
    config: dict[str, Any] | None = None,
    request_store: Any | None = None,
    storage_client: Any | None = None,
) -> APIDownloader:
    http_session = http_session or requests.Session()
    http_session.headers.update(
        {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
    )

    config = config or get_config(Path(__file__).parent / "config.yaml")
    league_ids = [str(x) for x in config["leagues"]]

    generate_fixture_requests_filtered = partial(
        generate_fixture_requests, league_ids=league_ids
    )

    handler = (
        ResponseHandler()
        .add_parser("schedule", parse_schedule_response)
        .add_parser("match_stats", parse_stats_response)
        .add_parser("player_stats", parse_stats_response)
        .add_request_generator("schedule", generate_fixture_requests_filtered)
    )

    downloader_kwargs: dict[str, Any] = {
        "name": name,
        "http_session": http_session,
        "request_limit": REQUEST_DAILY_LIMIT,
        "response_handler": handler,
    }
    if request_store is not None:
        downloader_kwargs["request_store"] = request_store
    if storage_client is not None:
        downloader_kwargs["storage_client"] = storage_client

    downloader = APIDownloader(**downloader_kwargs)

    return downloader


def start_download(downloader: APIDownloader, date: str) -> None:
    downloader.download_backlog()
    request = APIRequest(
        url=f"{BASE_URL}/fixtures",
        params={"date": date},
        type="schedule",
    )
    downloader.download(request)
