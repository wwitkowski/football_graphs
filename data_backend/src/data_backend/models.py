from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from data_backend.database.models import RequestDB, RequestStatus
from pydantic.dataclasses import dataclass


class APIRequest(BaseModel):
    url: str
    type: str
    params: dict[str, str] | None = None
    payload: dict[str, Any] | None = None


@dataclass
class StoredRequest:
    request: APIRequest
    name: str
    logical_date: str
    id: int | None = None

    def to_orm(self) -> RequestDB:
        """
        Convert this DownloadTask to the corresponding ORM model for persistence.

        Returns
        -------
        RequestDB
            The database representation of this request.
        """
        return RequestDB(
            name=self.name,
            logical_date=self.logical_date,
            url=self.request.url,
            params=self.request.params,
            payload=self.request.payload,
            type=self.request.type,
        )
    
    @classmethod
    def from_orm(cls, db_request: RequestDB) -> StoredRequest:
        """
        Create a StoredRequest instance from a RequestDB ORM object.

        Parameters
        ----------
        db_request : RequestDB
            The database request object to convert.

        Returns
        -------
        StoredRequest
            The corresponding StoredRequest instance.
        """
        api_request = APIRequest(
            url=db_request.url,
            type=db_request.type,
            params=db_request.params,
            payload=db_request.payload,
        )
        return cls(
            id=db_request.id,
            request=api_request,
            name=db_request.name,
            logical_date=db_request.logical_date,
        )


class APIResponse(BaseModel):
    body: str
    request: APIRequest
    path: str | None = None
    error: str | None = None
