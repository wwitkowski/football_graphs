from sqlmodel import select

from data_backend.database.models import RequestDB, RequestStatusEnum
from data_backend.database.requests import RequestStore
from data_backend.models import APIRequest


def test_add(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = APIRequest(
        url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
    )
    requests.add([r1], name="test_name")
    assert r1.id is not None


def test_get_pending(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = APIRequest(
        url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
    )
    r2 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "succeeded"},
        payload={"param": 2},
        status=RequestStatusEnum.SUCCEEDED,
    )
    r3 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "failed"},
        payload={"param": 3},
        status=RequestStatusEnum.FAILED,
    )
    requests.add([r1, r2, r3], name="test_name")

    r4 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "pending"},
        payload={"param": 4},
    )
    requests.add([r4], name="other_name")

    result = requests.get_pending(name="test_name")
    assert len(result) == 1
    assert result[0].url == r1.url
    assert result[0].type == r1.type
    assert result[0].params == r1.params
    assert result[0].payload == r1.payload


def test_get_today_count(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = APIRequest(
        url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
    )
    r2 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "succeeded"},
        payload={"param": 2},
        status=RequestStatusEnum.SUCCEEDED,
    )
    r3 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "failed"},
        payload={"param": 3},
        status=RequestStatusEnum.FAILED,
    )
    requests.add([r1, r2, r3], name="test_name")

    r4 = APIRequest(
        url="test.com",
        type="test",
        params={"status": "pending"},
        payload={"param": 4},
        status=RequestStatusEnum.SUCCEEDED,
    )
    requests.add([r4], name="other_name")

    result = requests.get_today_count(name="test_name")
    assert result == 2


def test_complete_request(sqlite_session_factory):
    requests = RequestStore(sqlite_session_factory)
    r1 = APIRequest(
        url="test.com", type="test", params={"status": "pending"}, payload={"param": 1}
    )
    requests.add([r1], name="test_name")

    status = RequestStatusEnum.SUCCEEDED
    requests.complete(r1, status)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r1.id)).one()
    assert result.status == status
