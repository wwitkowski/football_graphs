from unittest import mock

import pytest

from scripts.football_api.download_ongoing import main


@mock.patch("scripts.football_api.download_ongoing.run_download_football_api")
def test_main_with_valid_date(mock_run):
    test_args = ["2025-01-01"]
    with mock.patch("sys.argv", ["script.py"] + test_args):
        main()
    mock_run.assert_called_once_with("2025-01-01")


@mock.patch("scripts.football_api.download_ongoing.run_download_football_api")
def test_main_without_date(mock_run):
    with mock.patch("sys.argv", ["script.py"]):
        with pytest.raises(SystemExit):
            main()
    mock_run.assert_not_called()
