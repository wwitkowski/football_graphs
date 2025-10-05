import json

import boto3

from data_backend.aws import S3Client


def test_save_json_to_s3(fake_s3_bucket):
    client = S3Client(fake_s3_bucket)
    test_key = "test.json"
    test_data = {"foo": "bar", "number": 123}

    client.save_json(test_data, test_key)

    s3 = boto3.client("s3", region_name="us-east-1")
    obj = s3.get_object(Bucket=fake_s3_bucket, Key=test_key)
    body = obj["Body"].read().decode("utf-8")
    content_type = obj["ContentType"]

    assert json.loads(body) == test_data
    assert content_type == "application/json"
