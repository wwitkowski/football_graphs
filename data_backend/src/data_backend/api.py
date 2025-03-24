from typing import Any

from data_backend.download import APIDownloader


class FootballAPIClient:
    """Handles API interactions."""

    BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

    def __init__(self, api_key: str, request_limit: int = 100):
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        }
        self.downloader = APIDownloader(request_limit=request_limit)

    def fetch(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Fetches data from the API."""
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.downloader.download(url, headers=self.headers, params=params)
        return response.json()
