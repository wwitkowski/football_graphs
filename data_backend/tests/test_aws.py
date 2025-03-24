import json
from unittest import mock
from unittest.mock import MagicMock
from data_backend.aws import S3Client
import pytest
import boto3


@pytest.fixture
def mock_s3_client():
    """Mocks the S3 client inside S3Client."""
    mock_client = MagicMock()
    mock_client.put_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    return mock_client


@mock.patch("boto3.client")
def test_upload_json(mock_s3_client):
    """Tests that JSON data is uploaded successfully using the mocked S3 client."""
    test_data = {"message": "Hello, MinIO!"}
    key = "test.json"

    mock_s3_client.return_value = mock_s3_client
    s3_client = S3Client("test-bucket")
    s3_client.upload_json(test_data, key)

    expected_json_bytes = json.dumps(test_data).encode("utf-8")
    actual_body = mock_s3_client.put_object.call_args[1]["Body"]

    assert actual_body.getvalue() == expected_json_bytes
    mock_s3_client.put_object.assert_called_once_with(
        Bucket="test-bucket", Key=key, Body=actual_body, ContentType="application/json"
    )
