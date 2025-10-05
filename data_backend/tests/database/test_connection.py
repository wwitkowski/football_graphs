from data_backend.database.connection import get_db_url


def test_get_db_url_success(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("POSTGRES_HOST", "myhost")

    url = get_db_url()
    assert url == "postgresql+psycopg2://user:pass@myhost:5432/db"


def test_get_db_url_defaults_host(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass")
    monkeypatch.setenv("POSTGRES_DB", "db")

    url = get_db_url()
    assert url == "postgresql+psycopg2://user:pass@localhost:5432/db"
