from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlmodel import JSON, Field, SQLModel, String
from typing_extensions import Literal


class RequestStatusEnum(str, Enum):
    PENDING = "Pending"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


RequestStatus = Literal[
    RequestStatusEnum.PENDING, RequestStatusEnum.SUCCEEDED, RequestStatusEnum.FAILED
]


class RequestDB(SQLModel, table=True):  # type: ignore[call-arg]
    __tablename__ = "requests"

    id: int | None = Field(default=None, primary_key=True)
    url: str
    params: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    payload: dict[str, Any] | None = Field(default=None, sa_type=JSON)
    type: str | None = Field(default=None)
    status: RequestStatus = Field(default=RequestStatusEnum.PENDING, sa_type=String)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
