from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from data_backend.database.models import RequestDB, RequestStatus


class APIRequest(BaseModel):
    id: int | None = None
    url: str
    type: str
    params: dict[str, str] | None = None
    payload: dict[str, Any] | None = None
    status: RequestStatus | None = None
    is_historical: bool = False

    class Config:
        orm_mode = True

    def to_orm(self) -> RequestDB:
        """
        Convert this APIRequest to the corresponding ORM model for persistence.

        Returns
        -------
        RequestDB
            The database representation of this request.
        """
        return RequestDB(**self.dict())


class APIResponse(BaseModel):
    body: str
    request: APIRequest
    path: str | None = None
    error: str | None = None
