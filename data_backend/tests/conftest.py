import boto3
import pytest
import requests
from moto import mock_aws
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def test_engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def sqlite_session_factory(test_engine):
    return sessionmaker(bind=test_engine, class_=Session, expire_on_commit=False)


@pytest.fixture
def fake_s3_bucket():
    """Fixture to set up a mocked S3 bucket."""
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        bucket_name = "test-bucket"
        s3.create_bucket(Bucket=bucket_name)
        yield bucket_name


class FakeResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError("HTTP Error", response=self)
        else:
            return


class FakeHTTPSession:
    def __init__(self, response):
        self.response = response

    def get(self, *args, **kwargs):
        return self.response
