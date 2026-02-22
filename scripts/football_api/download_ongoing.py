import argparse
import logging
from collections.abc import Callable

from scripts.football_api.football_api import (
    APIDownloader,
    get_football_api_downloader,
    start_download,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(
    argv: list[str] | None = None,
    downloader_factory: Callable[[str], APIDownloader] = get_football_api_downloader,
) -> None:
    parser = argparse.ArgumentParser(
        description="Download football API data for a date"
    )
    parser.add_argument(
        "date", help="Date in YYYY-MM-DD format to download schedule for"
    )
    parser.add_argument(
        "name",
        help="""
            String name to identify this download process.
            Each download process downloads its own requests.
        """,
    )
    args = parser.parse_args(argv)
    logger.info(f"Starting download for {args.name}, date: {args.date}")
    downloader = downloader_factory(args.name)
    start_download(downloader, args.date)


if __name__ == "__main__":
    main()
