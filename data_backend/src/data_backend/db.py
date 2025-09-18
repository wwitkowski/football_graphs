import os
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, create_engine


def init_db(database_url: str) -> Session:
    engine = create_engine(database_url)
    return Session(engine)


@contextmanager
def get_db_session(db_url: str) -> Generator[Session, None, None]:
    """Context manager for DB sessions."""
    session = init_db(db_url)
    try:
        yield session
    finally:
        session.close()


def get_db_url() -> str:
    """Construct DB URL from environment variables."""
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST", "localhost")

    if not all([user, password, db]):
        raise EnvironmentError(
            "Missing one of POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB"
        )

    return f"postgresql+psycopg2://{user}:{password}@{host}:5432/{db}"
