import argparse
import os
from pathlib import Path
from typing import Any

import yaml

from data_backend.aws import S3Client
from scripts.football_api.football_api import FootballAPIClient


def _parse_args(arg_list: list[str] | None):
    parser = argparse.ArgumentParser()
    parser.add_argument("date")
    args = parser.parse_args(arg_list)
    return args


def get_db_url() -> str:
    """Construct the database URL from environment variables."""
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not all([user, password, db]):
        raise EnvironmentError(
            "Missing one of POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB"
        )

    return f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"


def get_config(path: Path) -> dict[str, Any]:
    """Load configuration from a yaml file."""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML config: {e}")


def run_download_football_api(
    date: str,
    config_path: str = "scripts/football_api/config.yaml",
    api_client=None,
    s3_client=None,
):
    """Download ongoing match data from the Football API and upload to S3."""
    config = get_config(Path(config_path))
    api_client = api_client or FootballAPIClient(
        api_key=os.environ["API_FOOTBALL_KEY"], db_url=get_db_url()
    )
    s3_client = s3_client or S3Client(bucket="raw-data")

    schedule_data = api_client.fetch("fixtures", {"date": date})
    s3_client.upload_json(schedule_data, f"{date}/schedule.json")

    filtered_fixtures = filter(
        lambda f: f["league"]["id"] in config["leagues"],
        schedule_data.get("response", []),
    )
    for fixture in filtered_fixtures:
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
