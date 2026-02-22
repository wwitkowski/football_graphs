import json

import boto3
from sqlmodel import select

from data_backend.api import APIDownloader
from data_backend.aws import S3Client
from data_backend.database.models import RequestDB
from data_backend.database.requests import RequestStore
from data_backend.handlers import ResponseHandler
from data_backend.models import APIRequest
from tests.conftest import FakeHTTPSession, FakeResponse


def test_download(fake_s3_bucket, sqlite_session_factory):
    test_key = "response.json"

    def handle(response):
        return {"message": response}, test_key

    fake_session = FakeHTTPSession(FakeResponse("OK", 200))
    handler = ResponseHandler().add_parser("test", handle)

    downloader = APIDownloader(
        name="test_name",
        http_session=fake_session,
        response_handler=handler,
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Succeeded"
    assert result.id == req.id
    assert result.type == req.type
    assert result.url == req.url

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=test_key)
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
        http_session=fake_session,
        response_handler=handler,
        request_store=requests,
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    r1 = APIRequest(url="http://example.com", type="test")
    r2 = APIRequest(url="http://example.org", type="other_test")
    requests.add([r1], name="test_name")
    requests.add([r2], name="other_name")
    downloader.download_backlog()

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r2.id)).one()

    assert result.status == "Pending"
    assert result.id == r2.id
    assert result.type == r2.type
    assert result.url == r2.url

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == r1.id)).one()

    assert result.status == "Succeeded"
    assert result.id == r1.id
    assert result.type == r1.type
    assert result.url == r1.url

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=test_key)
    body = obj["Body"].read().decode("utf-8")

    assert json.loads(body) == {"message": "OK"}


def test_download_requester_error(fake_s3_bucket, sqlite_session_factory):
    fake_session = FakeHTTPSession(FakeResponse("NOT OK", 404))

    downloader = APIDownloader(
        name="test_name",
        http_session=fake_session,
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Failed"


def test_download_limit_reached(fake_s3_bucket, sqlite_session_factory):
    fake_session = FakeHTTPSession(FakeResponse("OK", 200))

    downloader = APIDownloader(
        name="test_name",
        http_session=fake_session,
        request_limit=0,
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Pending"
