from datetime import datetime, timezone, date
from data_backend.database.connection import get_db_url
from data_backend.database.models import RequestStatusEnum
from data_backend.database.models import RequestDB
from data_backend.models import APIRequest
from sqlalchemy import create_engine
from sqlmodel import Session, func, select
from sqlalchemy.orm import sessionmaker


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(get_db_url()),
    class_=Session, 
    expire_on_commit=False
)


class RequestStore:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_pending(self) -> list[APIRequest]:
        with self.session_factory() as session:
            stmt = select(RequestDB).where(RequestDB.status == RequestStatusEnum.PENDING)
            result = session.exec(stmt).all()
            return [APIRequest.from_orm(r) for r in result]
        
    def get_today_count(self) -> int:
        today = date.today()
        with self.session_factory() as session:
            stmt = (
                select(func.count(RequestDB.id))
                .where(RequestDB.updated_at >= today)
                .where(RequestDB.status != RequestStatusEnum.PENDING)
            )
            return session.exec(stmt).one()
        
    def add(self, api_requests: list[APIRequest]) -> list[APIRequest]:
        db_requests = [r.to_orm() for r in api_requests]
        with self.session_factory() as session:
            session.add_all(db_requests)
            session.commit()
        
        for api_req, db_req in zip(api_requests, db_requests):
            api_req.id = db_req.id

    def complete(self, api_request: APIRequest, status: RequestStatusEnum) -> None:
        with self.session_factory() as session:
            db_request = session.get(RequestDB, api_request.id)
            db_request.status = status
            db_request.updated_at = datetime.now(timezone.utc)
            session.commit()
    