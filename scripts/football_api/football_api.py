from typing import Any, Type

import requests

from data_backend.api import APIDownloader
from data_backend.db import get_db_session


class FootballAPIClient:
    """Handles API interactions with the Football API."""

    BASE_URL: str = "https://api-football-v1.p.rapidapi.com/v3"

    def __init__(
        self,
        api_key: str,
        db_url: str,
        request_limit: int = 100,
        downloader_cls: Type[APIDownloader] = APIDownloader,
    ) -> None:
        self.db_url = db_url
        self.request_limit = request_limit
        self.downloader_cls = downloader_cls

        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        }
        self.http_session = requests.Session()
        self.http_session.headers.update(self.headers)

    def fetch(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Fetch data from the API and return parsed JSON."""
        url = f"{self.BASE_URL}/{endpoint}"
        with get_db_session(self.db_url) as session:
            downloader = self.downloader_cls(
                session,
                request_limit=self.request_limit,
                http_session=self.http_session,
                service_name="football_api_client",
            )
            response = downloader.download(url, params=params)
            return response.json()
