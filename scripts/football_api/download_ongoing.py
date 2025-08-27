import argparse
import os

from data_backend.aws import S3Client
from scripts.football_api.football_api import FootballAPIClient


def _parse_args(arg_list: list[str] | None):
    parser = argparse.ArgumentParser()
    parser.add_argument("date")
    args = parser.parse_args(arg_list)
    return args


def get_db_url() -> str:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "localhost")

    return f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"


def run_download_football_api(date: str):
    api_client = FootballAPIClient(
        api_key=os.environ.get("API_FOOTBALL_KEY"),
        db_url=get_db_url(),
    )
    s3_client = S3Client(bucket="raw-data")

    schedule_data = api_client.fetch("fixtures", {"date": date})
    s3_client.upload_json(schedule_data, f"{date}/schedule.json")

    for fixture in schedule_data.get("response", []):
        fixture_id = fixture["fixture"]["id"]

        for endpoint, filename in [
            ("fixtures/statistics", "fixture_statistics"),
            ("fixtures/players", "player_statistics"),
        ]:
            data = api_client.fetch(endpoint, {"fixture": fixture_id})
            s3_client.upload_json(data, f"{date}/{fixture_id}_{filename}.json")


def main(arg_list: list[str] | None = None):
    args = _parse_args(arg_list)
    run_download_football_api(args.date)


if __name__ == "__main__":
    main()
