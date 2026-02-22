from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, func, select

from data_backend.database.connection import get_db_url
from data_backend.database.models import RequestDB, RequestStatusEnum
from data_backend.models import APIRequest

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

    def get_pending(self, name: str) -> list[APIRequest]:
        """
        Retrieve all pending requests, optionally filtering by historical or ongoing.

        Parameters
        ----------
        historical : bool, optional
            If True, only returns historical requests. If False (default), returns
            ongoing requests.

        Returns
        -------
        list of APIRequest
            A list of APIRequest objects with status ``PENDING`` and matching the
            specified historical flag.
        """
        with self.session_factory() as session:
            stmt = select(RequestDB).where(
                RequestDB.status == RequestStatusEnum.PENDING,
                RequestDB.name == name,
            )
            result = session.exec(stmt).all()
            return [APIRequest.from_orm(r) for r in result]

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

    def add(self, api_requests: list[APIRequest], name: str) -> None:
        """
        Insert new API requests into the database.

        Parameters
        ----------
        api_requests : list of APIRequest
            A list of APIRequest objects to persist in the database.
        """
        db_requests = [r.to_orm(name=name) for r in api_requests]
        with self.session_factory() as session:
            session.add_all(db_requests)
            session.commit()

        for api_req, db_req in zip(api_requests, db_requests):
            api_req.id = db_req.id

    def complete(self, api_request: APIRequest, status: RequestStatusEnum) -> None:
        """
        Mark a request as completed by updating its status and updated_at timestamp.

        Parameters
        ----------
        api_request : APIRequest
            The request object to update.
        status : RequestStatusEnum
            The final status to assign to the request.
        """
        with self.session_factory() as session:
            db_request = session.get(RequestDB, api_request.id)
            db_request.status = status
            db_request.updated_at = datetime.now(timezone.utc)
            session.commit()
