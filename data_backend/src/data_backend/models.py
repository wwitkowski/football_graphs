from __future__ import annotations
from typing import Any
from data_backend.database.models import RequestDB, RequestStatus
from pydantic import BaseModel


class APIRequest(BaseModel):
    id: int | None
    url: str
    params: dict[str, str] | None
    payload: dict[str, Any] | None
    type: str | None
    status: RequestStatus | None

    class Config:
        orm_mode = True
        
    def to_orm(self) -> RequestDB:
        return RequestDB(**self.dict())


class APIResponse(BaseModel):
    body: str
    request: APIRequest
    path: str | None
    error: str | None
