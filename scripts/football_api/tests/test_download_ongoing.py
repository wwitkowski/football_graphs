from scripts.football_api import download_ongoing


class FakeDownloader:
    def __init__(self):
        self.backlog_called = False
        self.requests = []
        self.download_called = False

    def download_backlog(self):
        self.backlog_called = True

    def add(self, request):
        self.requests.append(request)

    def download(self):
        self.download_called = True
        

def test_main_parses_args_and_starts_download():
    calls = {}
    fake_downloader = FakeDownloader()

    def fake_get_downloader(name, date):
        calls["name"] = name
        calls["date"] = date
        return fake_downloader

    download_ongoing.main(
        argv=["2026-02-20", "ongoing-job"],
        downloader_factory=fake_get_downloader,
    )

    assert calls["name"] == "ongoing-job"
    assert calls["date"] == "2026-02-20"
    assert fake_downloader.backlog_called is True
    assert fake_downloader.download_called is True
    assert len(fake_downloader.requests) == 5
    request_dates = [r.params["date"] for r in fake_downloader.requests]
    assert request_dates == [
        "2026-02-19",
        "2026-02-20",
        "2026-02-21",
        "2026-02-22",
        "2026-02-23",
    ]
