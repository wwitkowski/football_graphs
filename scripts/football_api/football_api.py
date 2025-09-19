import logging
import os
from pathlib import Path

import requests
from data_backend.api import APIDownloader
from data_backend.aws import S3Client
from data_backend.config import get_config
from data_backend.db import get_db_session, get_db_url
from data_backend.models import Request

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"
API_KEY = os.environ.get("API_FOOTBALL_KEY")
API_HOST = "api-football-v1.p.rapidapi.com"
REQUEST_DAILY_LIMIT = 100

logger = logging.getLogger(__name__)


def handle_schedule_response(
    data: dict, date: str, league_ids: list[int], s3_client: S3Client
) -> list[Request]:
    """Upload schedule to S3, return fixture requests to enqueue."""
    logger.info(f"Uploading {date}/schedule.json to S3")
    s3_client.upload_json(data, f"{date}/schedule.json")
    stats_requests = []
    for fixture in data.get("response", []):
        league_id = fixture.get("league", {}).get("id")
        fixture_id = fixture.get("fixture", {}).get("id")
        if not fixture_id or league_id not in league_ids:
            continue
        stats_requests.extend(
            [
                Request(
                    endpoint=f"{BASE_URL}/fixtures/statistics",
                    params={"fixture": fixture_id},
                    request_metadata={"date": date},
                ),
                Request(
                    endpoint=f"{BASE_URL}/fixtures/players",
                    params={"fixture": fixture_id},
                    request_metadata={"date": date},
                ),
            ]
        )

    return stats_requests


def handle_stats_response(data: dict, date: str, s3_client: S3Client) -> None:
    """Upload fixture statistics or player stats to S3."""
    fixture_id = data.get("parameters", {}).get("fixture")
    filename = data.get("get")
    if not fixture_id or not filename:
        logger.warning("Invalid stats response, missing fixture ID or type")
        return
    filename = filename.split("/")[-1]
    path = f"{date}/{fixture_id}_{filename}.json"
    logger.info(f"Uploading {path} to S3")
    s3_client.upload_json(data, path)


def run_download_football_api(date: str) -> None:
    """Workflow: schedule request -> fixture requests -> uploads."""
    http_session = requests.Session()
    http_session.headers.update(
        {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}
    )
    config = get_config(Path("scripts/config/football_api/config.yaml"))
    allowed_league_ids = config.get("leagues", [])
    s3 = S3Client(bucket="raw-data")

    with get_db_session(get_db_url()) as db_session:
        downloader = APIDownloader(
            db_session, http_session=http_session, request_limit=REQUEST_DAILY_LIMIT
        )

        schedule_request = Request(
            endpoint=f"{BASE_URL}/fixtures",
            params={"date": date},
            request_metadata={"type": "schedule", "date": date},
        )
        downloader.add([schedule_request])

        for req, resp in downloader.download_next(on_error="continue"):
            data = resp.json()
            if data.get("get") == "fixtures":
                new_requests = handle_schedule_response(
                    data, req.request_metadata["date"], allowed_league_ids, s3
                )
                downloader.add(new_requests)
            else:
                handle_stats_response(data, req.request_metadata["date"], s3)
