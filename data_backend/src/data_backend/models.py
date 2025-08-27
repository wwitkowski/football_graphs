from datetime import date

from sqlmodel import Field, Session, SQLModel, func, select
from typing_extensions import Literal

RequestStatus = Literal["Pending", "Succeeded", "Failed"]


class Request(SQLModel, table=True):  # type: ignore[call-arg]
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
