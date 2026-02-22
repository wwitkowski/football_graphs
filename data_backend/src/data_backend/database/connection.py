import os


def get_db_url() -> str:
    """Construct DB URL from environment variables."""
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "localhost")

    return f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"
