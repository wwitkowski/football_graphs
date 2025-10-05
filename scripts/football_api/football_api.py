from functools import partial
import json
import logging
import os
from pathlib import Path
from typing import Any

from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest
import requests
from data_backend.api import APIDownloader


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
        if not fixture_id or league_id not in league_ids:
            continue
        requests.extend(
            [
                APIRequest(
                    endpoint=f"{BASE_URL}/fixtures/statistics",
                    params={"fixture": fixture_id},
                    type="match_stats",
                ),
                APIRequest(
                    endpoint=f"{BASE_URL}/fixtures/players",
                    params={"fixture": fixture_id},
                    type="player_stats",
                ),
            ]
        )
    return requests


def parse_stats_response(body: str, ) -> tuple[dict[str, Any], str]:
    data = json.loads(body)
    fixture_id = data.get("parameters", {}).get("fixture")
    endpoint = data.get("get", "")
    if not fixture_id or not endpoint:
        logger.warning("Stats response missing 'fixture' parameter or 'get' field")
    filename = endpoint.split("/")[-1]
    return data, f"{fixture_id}_{filename}.json"



def run_download_football_api(date: str) -> None:
    http_session = requests.Session()
    http_session.headers.update(
        {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
    )

    generate_fixture_requests_filtered = partial(
        generate_fixture_requests, league_ids=["39", "140", "78", "135", "61"])
    

    handler = ResponseHandler() \
        .add_parser("schedule", parse_schedule_response) \
        .add_parser("match_stats", parse_stats_response) \
        .add_parser("player_stats", parse_stats_response) \
        .add_generator("schedule", generate_fixture_requests_filtered)

    downloader = APIDownloader(
        http_session=http_session,
        request_limit=REQUEST_DAILY_LIMIT,
        response_handler=handler
    )

    request = APIRequest(
        endpoint=f"{BASE_URL}/fixtures",
        params={"date": date},
        type="schedule",
    )

    downloader.download(request)
