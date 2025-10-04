import json
import boto3
from data_backend.aws import S3Client
from data_backend.database.models import RequestDB
from data_backend.database.requests import RequestStore
from data_backend.handlers import ResponseHandler
from data_backend.requester import HTTPRequester
from sqlmodel import select
from tests.conftest import FakeHTTPSession, FakeResponse

from data_backend.api import APIDownloader
from data_backend.models import APIRequest


def test_download(fake_s3_bucket, sqlite_session_factory):

    test_key = "response.json"
    def handle(response):
        return {"message": response}, test_key
    
    
    fake_session = FakeHTTPSession(FakeResponse("OK", 200))
    handler = ResponseHandler().add_parser("test", handle)

    downloader = APIDownloader(
        response_handler=handler,
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
        requester=HTTPRequester(http_session=fake_session),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Succeeded"
    assert result.url == req.url

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=test_key)
    body = obj["Body"].read().decode("utf-8")

    assert json.loads(body) == {"message": "OK"}


def test_download_requester_error(fake_s3_bucket, sqlite_session_factory):

    fake_session = FakeHTTPSession(FakeResponse("NOT OK", 404))

    downloader = APIDownloader(
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
        requester=HTTPRequester(http_session=fake_session),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Failed"


def test_download_limit_reached(fake_s3_bucket, sqlite_session_factory):

    fake_session = FakeHTTPSession(FakeResponse("OK", 200))

    downloader = APIDownloader(
        response_handler=ResponseHandler(),
        request_store=RequestStore(sqlite_session_factory),
        storage_client=S3Client(bucket_name=fake_s3_bucket),
        requester=HTTPRequester(http_session=fake_session, request_limit=1, request_count=1),
    )

    req = APIRequest(url="http://example.com", type="test")
    downloader.download(req)

    with sqlite_session_factory() as session:
        result = session.exec(select(RequestDB).where(RequestDB.id == req.id)).one()

    assert result.status == "Pending"