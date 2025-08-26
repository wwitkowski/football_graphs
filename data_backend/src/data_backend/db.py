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
