import argparse
import logging

from scripts.football_api.football_api import run_download_football_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Download football API data for a date"
    )
    parser.add_argument(
        "date", help="Date in YYYY-MM-DD format to download schedule for"
    )
    args = parser.parse_args()
    logger.info(f"Starting download for date: {args.date}")
    run_download_football_api(args.date)


if __name__ == "__main__":
    main()
