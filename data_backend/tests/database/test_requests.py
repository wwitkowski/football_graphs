from sqlmodel import select

from data_backend.database.models import RequestDB, RequestStatusEnum
from data_backend.database.requests import RequestStore
from data_backend.models import APIRequest, StoredRequest


def test_add(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    api_req = APIRequest(
        url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
    )
    req = StoredRequest(request=api_req, name="test_name", logical_date="2026-02-20")
    requests.add(req)
    assert req.id is not None


def test_get_pending(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = StoredRequest(
        request=APIRequest(
            url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    r2 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "succeeded"},
            payload={"param": 2},
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    r3 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "failed"},
            payload={"param": 3},
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    requests.add(r1)
    requests.add(r2)
    requests.add(r3)
    requests.complete(r2, RequestStatusEnum.SUCCEEDED)
    requests.complete(r3, RequestStatusEnum.FAILED)

    r4 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "pending"},
            payload={"param": 4},
        ),
        name="other_name",
        logical_date="2026-02-20",
    )
    requests.add(r4)

    result = requests.get_pending(name="test_name")
    assert len(result) == 1
    assert result[0].request.url == r1.request.url
    assert result[0].request.type == r1.request.type
    assert result[0].request.params == r1.request.params
    assert result[0].request.payload == r1.request.payload
    assert result[0].logical_date == "2026-02-20"


def test_get_today_count(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = StoredRequest(
        request=APIRequest(
            url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    r2 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "succeeded"},
            payload={"param": 2},
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    r3 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "failed"},
            payload={"param": 3},
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    requests.add(r1)
    requests.add(r2)
    requests.add(r3)
    requests.complete(r2, RequestStatusEnum.SUCCEEDED)
    requests.complete(r3, RequestStatusEnum.FAILED)

    r4 = StoredRequest(
        request=APIRequest(
            url="test.com",
            type="test",
            params={"status": "pending"},
            payload={"param": 4},
        ),
        name="other_name",
        logical_date="2026-02-20",
    )
    requests.add(r4)
    requests.complete(r4, RequestStatusEnum.SUCCEEDED)

    result = requests.get_today_count(name="test_name")
    assert result == 2


def test_complete_request(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = StoredRequest(
        request=APIRequest(
            url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
        ),
        name="test_name",
        logical_date="2026-02-20",
    )
    requests.add(r1)

    status = RequestStatusEnum.SUCCEEDED
    requests.complete(r1, status)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r1.id)).one()
    assert result.status == status
