import json
from typing import Any

import boto3


class S3Client:
    """Encapsulates S3 client."""

    def __init__(self, bucket_name: str, endpoint: str | None = None):
        self.s3_client = boto3.client("s3", endpoint_url=endpoint)  # "http://minio:9000"
        self.bucket_name = bucket_name

    def save_json(self, data: dict[str, Any], key: str):
        json_bytes = json.dumps(data)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json_bytes.encode("utf-8"),
            ContentType="application/json",
        )
