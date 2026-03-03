import json

import boto3
from sqlmodel import select

from data_backend.api import APIDownloader
from data_backend.aws import S3Client
from data_backend.database.models import RequestDB
from data_backend.database.requests import RequestStore
from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest, StoredRequest
from tests.conftest import FakeHTTPSession, FakeResponse


def test_download(fake_s3_bucket, sqlite_session_factory):
    test_key = "response.json"

    def handle(response):
        return {"message": response}, test_key

    fake_session = FakeHTTPSession(FakeResponse("OK", 200))
    handler = ResponseHandler().add_parser("test", handle)

    downloader = APIDownloader(
        name="test_name",
        logical_date="2026-02-20",
        http_session=fake_session,
        response_handler=handler,
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.url == req.url)).one()

    assert result.status == "Succeeded"
    assert result.type == req.type
    assert result.url == req.url
    assert result.logical_date == "2026-02-20"

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=f"2026-02-20/{test_key}")
    body = obj["Body"].read().decode("utf-8")

    assert json.loads(body) == {"message": "OK"}


def test_download_backlog(fake_s3_bucket, sqlite_session_factory):
    test_key = "response.json"

    def handle(response):
        return {"message": response}, test_key

    fake_session = FakeHTTPSession(FakeResponse("OK", 200))
    handler = ResponseHandler().add_parser("test", handle)
    requests = RequestStore(sqlite_session_factory)

    downloader = APIDownloader(
        name="test_name",
        logical_date="2026-02-21",
        http_session=fake_session,
        response_handler=handler,
        request_store=requests,
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    r1 = StoredRequest(
        request=APIRequest(url="http://example.com", type="test"),
        name="test_name",
        logical_date="2026-02-20",
    )
    r2 = StoredRequest(
        request=APIRequest(url="http://example.org", type="other_test"),
        name="other_name",
        logical_date="2026-02-20",
    )
    requests.add(r1)
    requests.add(r2)
    downloader.download_backlog()

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r2.id)).one()

    assert result.status == "Pending"
    assert result.id == r2.id
    assert result.type == r2.request.type
    assert result.url == r2.request.url

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r1.id)).one()

    assert result.status == "Succeeded"
    assert result.id == r1.id
    assert result.type == r1.request.type
    assert result.url == r1.request.url
    assert result.logical_date == "2026-02-20"

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=f"2026-02-20/{test_key}")
    body = obj["Body"].read().decode("utf-8")

    assert json.loads(body) == {"message": "OK"}


def test_download_requester_error(fake_s3_bucket, sqlite_session_factory):
    fake_session = FakeHTTPSession(FakeResponse("NOT OK", 404))

    downloader = APIDownloader(
        name="test_name",
        logical_date="2026-02-20",
        http_session=fake_session,
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.url == req.url)).one()

    assert result.status == "Failed"


def test_download_limit_reached(fake_s3_bucket, sqlite_session_factory):
    fake_session = FakeHTTPSession(FakeResponse("OK", 200))

    downloader = APIDownloader(
        name="test_name",
        logical_date="2026-02-20",
        http_session=fake_session,
        request_limit=0,
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.url == req.url)).one()

    assert result.status == "Pending"
