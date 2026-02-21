from scripts.football_api import download_ongoing


def test_main_parses_args_and_starts_download():
    calls = {}

    class FakeDownloader:
        def __init__(self):
            self.backlog_called = False
            self.requests = []

        def download_backlog(self):
            self.backlog_called = True

        def download(self, request):
            self.requests.append(request)

    fake_downloader = FakeDownloader()

    def fake_get_downloader(name):
        calls["name"] = name
        return fake_downloader

    download_ongoing.main(
        argv=["2026-02-20", "ongoing-job"],
        downloader_factory=fake_get_downloader,
    )

    assert calls["name"] == "ongoing-job"
    assert fake_downloader.backlog_called is True
    assert len(fake_downloader.requests) == 1
    request = fake_downloader.requests[0]
    assert request.type == "schedule"
    assert request.params == {"date": "2026-02-20"}


def test_main_logs_start_message(caplog):
    class FakeDownloader:
        def download_backlog(self):
            return None

        def download(self, _request):
            return None

    fake_downloader = FakeDownloader()

    with caplog.at_level("INFO"):
        download_ongoing.main(
            argv=["2026-02-20", "my-name"],
            downloader_factory=lambda name: fake_downloader,
        )

    assert "Starting download for my-name, date: 2026-02-20" in caplog.text
