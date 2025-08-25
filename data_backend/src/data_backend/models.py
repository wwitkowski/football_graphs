from datetime import date
from typing_extensions import Literal
from sqlmodel import Field, Session, SQLModel, create_engine, select, func


RequestStatus = Literal["Pending", "Succeeded", "Failed"]

class Request(SQLModel, table=True):
    __tablename__ = "requests"
    
    id: int | None = Field(default=None, primary_key=True)
    url: str
    status: str = Field(default="Pending")
    created_by: str
    created_at: date | None = None
    
    @classmethod
    def get_today_count(cls, session: Session) -> int:
        today = date.today()
        stmt = select(func.count()).where(cls.created_at == today)
        return session.exec(stmt).one()

def init_db(database_url: str) -> Session:
    engine = create_engine(database_url)
    return Session(engine)
