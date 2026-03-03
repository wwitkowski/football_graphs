from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, func, select

from data_backend.database.connection import get_db_url
from data_backend.database.models import RequestDB, RequestStatusEnum
from data_backend.models import StoredRequest

DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(get_db_url()), class_=Session, expire_on_commit=False
)


class RequestStore:
    """
    A data access layer for managing API request records in the database.

    Provides methods to fetch, insert, update, and count
    requests stored in the `requests` table.
    """

    def __init__(self, session_factory: sessionmaker = DEFAULT_SESSION_FACTORY) -> None:
        """
        Initialize the RequestStore with a session factory.

        Parameters
        ----------
        session_factory : sessionmaker, optional
            A callable that returns a SQLAlchemy/SQLModel session.
            Defaults to a sessionmaker bound to the application database.
        """
        self.session_factory = session_factory

    def get_pending(self, name: str) -> list[StoredRequest]:
        """
        Retrieve all pending requests, optionally filtering by historical or ongoing.

        Parameters
        ----------
        name : str
            The name of the request batch to filter by.

        Returns
        -------
        list of StoredRequest
            A list of StoredRequest objects with status ``PENDING`` and matching the
            specified name.
        """
        with self.session_factory() as session:
            stmt = select(RequestDB).where(
                RequestDB.status == RequestStatusEnum.PENDING,
                RequestDB.name == name,
            )
            result = session.exec(stmt).all()
            return [StoredRequest.from_orm(r) for r in result]

    def get_today_count(self, name: str) -> int:
        """
        Count the number of non-pending requests updated today.

        Returns
        -------
        int
            The number of completed (non-pending) requests that have
            been updated since the start of the current day.
        """
        today = date.today()
        with self.session_factory() as session:
            stmt = select(func.count(RequestDB.id)).where(
                RequestDB.updated_at >= today,
                RequestDB.name == name,
                RequestDB.status != RequestStatusEnum.PENDING,
            )
            return session.exec(stmt).one()

    def add(self, request: StoredRequest) -> None:
        """
        Insert new API requests into the database.

        Parameters
        ----------
        request : StoredRequest
            The request object to be added to the database. The `id` field will be
            populated after insertion.
        """
        db_request = request.to_orm()
        with self.session_factory() as session:
            session.add(db_request)
            session.commit()
        request.id = db_request.id

    def complete(self, request: StoredRequest, status: RequestStatusEnum) -> None:
        """
        Mark a request as completed by updating its status and updated_at timestamp.

        Parameters
        ----------
        request : StoredRequest
            The request object to update.
        status : RequestStatusEnum
            The final status to assign to the request.
        """
        with self.session_factory() as session:
            db_request = session.get(RequestDB, request.id)
            db_request.status = status
            db_request.updated_at = datetime.now(timezone.utc)
            session.commit()
